import { isPlatformBrowser } from '@angular/common';
import {
  afterNextRender,
  Component,
  computed,
  DestroyRef,
  effect,
  ElementRef,
  inject,
  input,
  PLATFORM_ID,
  signal,
  untracked,
  viewChild,
} from '@angular/core';
import {
  LucideChevronLeft,
  LucideChevronRight,
  LucideExternalLink,
  LucideZoomIn,
  LucideZoomOut,
} from '@lucide/angular';

import { FolioTarget } from '../../data-access/reading-tree';
import {
  isAbortError,
  PageRect,
  PDF_LOADER,
  PdfDocument,
  RenderedPage,
} from '../../data-access/pdf/pdf-port';

const ZOOMS = [0.75, 1, 1.25, 1.5, 2] as const;
const DEFAULT_ZOOM_INDEX = 1;
const PAGE_PADDING = 16;
const MIN_PAGE_WIDTH = 240;
const FALLBACK_WIDTH = 640;
const WIDTH_STEP = 8; // re-render only when the width changes by a visible amount
const MAX_CHIPS = 12;

type FolioStatus = 'loading' | 'ready' | 'error';

interface RenderedView {
  readonly page: number;
  readonly view: RenderedPage;
}

/**
 * "Folio": the page of the original PDF with the cited passage highlighted like a marker.
 * Only the byte ranges of the pages shown are downloaded (see PdfJsLoader).
 */
@Component({
  selector: 'drtc-folio',
  imports: [LucideChevronLeft, LucideChevronRight, LucideExternalLink, LucideZoomIn, LucideZoomOut],
  templateUrl: './folio.html',
  styleUrl: './folio.css',
  host: { class: 'block h-full' },
})
export class Folio {
  readonly sourceUrl = input.required<string>();
  readonly fileName = input('');
  readonly target = input<FolioTarget | null>(null);

  private readonly loader = inject(PDF_LOADER);
  private readonly platformId = inject(PLATFORM_ID);
  private readonly destroyRef = inject(DestroyRef);
  private readonly canvas = viewChild.required<ElementRef<HTMLCanvasElement>>('canvas');
  private readonly viewport = viewChild.required<ElementRef<HTMLElement>>('viewport');

  private readonly document = signal<PdfDocument | null>(null);
  private readonly containerWidth = signal(0);
  private readonly attempt = signal(0);
  private readonly zoomIndex = signal(DEFAULT_ZOOM_INDEX);
  private readonly renderedView = signal<RenderedView | null>(null);

  protected readonly status = signal<FolioStatus>('loading');
  protected readonly page = signal(1);
  protected readonly numPages = computed(() => this.document()?.numPages ?? 0);
  protected readonly zoomLabel = computed(() => `${Math.round(ZOOMS[this.zoomIndex()] * 100)} %`);
  protected readonly canZoomOut = computed(() => this.zoomIndex() > 0);
  protected readonly canZoomIn = computed(() => this.zoomIndex() < ZOOMS.length - 1);
  protected readonly canPrevious = computed(() => this.page() > 1);
  protected readonly canNext = computed(() => this.page() < this.numPages());

  private readonly cssWidth = computed(() => {
    const available = Math.max(
      MIN_PAGE_WIDTH,
      (this.containerWidth() || FALLBACK_WIDTH) - 2 * PAGE_PADDING,
    );
    return Math.max(
      MIN_PAGE_WIDTH,
      Math.round((available * ZOOMS[this.zoomIndex()]) / WIDTH_STEP) * WIDTH_STEP,
    );
  });

  protected readonly pageSize = computed(() => {
    const shown = this.renderedView();
    return shown?.page === this.page()
      ? { width: shown.view.cssWidth, height: shown.view.cssHeight }
      : null;
  });

  /** Highlight rectangles of the shown page (empty until that page has been drawn). */
  protected readonly marks = computed((): readonly PageRect[] => {
    const shown = this.renderedView();
    const target = this.target();
    if (!shown || shown.page !== this.page() || !target) return [];
    return target.boxes
      .filter((box) => box.page === shown.page)
      .map((box) => shown.view.toRect(box));
  });

  protected readonly chips = computed(() => {
    const target = this.target();
    if (!target || target.pageEnd <= target.pageStart) return [];
    const last = Math.min(target.pageEnd, target.pageStart + MAX_CHIPS - 1);
    return Array.from({ length: last - target.pageStart + 1 }, (_, i) => target.pageStart + i);
  });

  protected readonly pagesLabel = computed(() => {
    const target = this.target();
    if (!target) return '';
    return target.pageStart === target.pageEnd
      ? `p. ${target.pageStart}`
      : `pp. ${target.pageStart}-${target.pageEnd}`;
  });

  protected readonly canvasLabel = computed(() => {
    const name = this.fileName() ? ` del PDF «${this.fileName()}»` : ' del PDF';
    const base = `Página ${this.page()} de ${this.numPages()}${name}.`;
    return this.marks().length > 0 ? `${base} El pasaje citado está resaltado.` : base;
  });

  protected readonly announcement = computed(() =>
    this.status() === 'ready' ? `Página ${this.page()} de ${this.numPages()}` : '',
  );

  constructor() {
    afterNextRender(() => this.observeWidth());
    this.openDocumentEffect();
    this.followTargetEffect();
    this.renderEffect();
  }

  protected goTo(page: number): void {
    const total = this.numPages();
    if (total > 0) this.page.set(Math.min(Math.max(1, Math.trunc(page)), total));
  }

  protected onPageInput(event: Event): void {
    const value = Number((event.target as HTMLInputElement).value);
    if (Number.isFinite(value)) this.goTo(value);
    (event.target as HTMLInputElement).value = String(this.page());
  }

  protected zoomIn(): void {
    this.zoomIndex.update((i) => Math.min(i + 1, ZOOMS.length - 1));
  }

  protected zoomOut(): void {
    this.zoomIndex.update((i) => Math.max(i - 1, 0));
  }

  protected resetZoom(): void {
    this.zoomIndex.set(DEFAULT_ZOOM_INDEX);
  }

  protected retry(): void {
    this.attempt.update((n) => n + 1);
  }

  private observeWidth(): void {
    const element = this.viewport().nativeElement;
    this.containerWidth.set(Math.round(element.clientWidth));
    if (typeof ResizeObserver === 'undefined') return;
    const observer = new ResizeObserver((entries) => {
      const width = entries[0]?.contentRect.width ?? 0;
      if (width > 0) this.containerWidth.set(Math.round(width));
    });
    observer.observe(element);
    this.destroyRef.onDestroy(() => observer.disconnect());
  }

  private openDocumentEffect(): void {
    effect((onCleanup) => {
      const url = this.sourceUrl();
      this.attempt();
      if (!isPlatformBrowser(this.platformId)) return;
      const controller = new AbortController();
      let opened: PdfDocument | null = null;
      untracked(() => {
        this.status.set('loading');
        this.document.set(null);
        this.renderedView.set(null);
      });
      this.loader
        .open(url, controller.signal)
        .then((doc) => {
          if (controller.signal.aborted) {
            doc.destroy();
            return;
          }
          opened = doc;
          this.document.set(doc);
        })
        .catch((error: unknown) => {
          if (!isAbortError(error) && !controller.signal.aborted) this.status.set('error');
        });
      onCleanup(() => {
        controller.abort();
        opened?.destroy();
      });
    });
  }

  /** Whenever a new passage is chosen (or the document finishes loading), show its first page. */
  private followTargetEffect(): void {
    effect(() => {
      const target = this.target();
      const total = this.numPages();
      if (!target) return;
      untracked(() =>
        this.page.set(
          total > 0 ? Math.min(Math.max(1, target.pageStart), total) : target.pageStart,
        ),
      );
    });
  }

  private renderEffect(): void {
    effect((onCleanup) => {
      const doc = this.document();
      const page = this.page();
      const width = this.cssWidth();
      if (!doc || page < 1 || page > doc.numPages) return;
      const controller = new AbortController();
      onCleanup(() => controller.abort());
      doc
        .render(page, this.canvas().nativeElement, width, controller.signal)
        .then((view) => {
          this.renderedView.set({ page, view });
          this.status.set('ready');
          this.scrollToPassage(view, page);
        })
        .catch((error: unknown) => {
          if (!isAbortError(error) && !controller.signal.aborted) this.status.set('error');
        });
    });
  }

  private scrollToPassage(view: RenderedPage, page: number): void {
    const boxes = this.target()?.boxes.filter((box) => box.page === page) ?? [];
    const top = boxes.length > 0 ? Math.min(...boxes.map((box) => view.toRect(box).top)) : 0;
    const reduced =
      typeof matchMedia === 'function' && matchMedia('(prefers-reduced-motion: reduce)').matches;
    this.viewport().nativeElement.scrollTo?.({
      top: Math.max(0, top - 96),
      behavior: reduced ? 'auto' : 'smooth',
    });
  }
}
