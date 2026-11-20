import {
  afterRenderEffect,
  Component,
  computed,
  DestroyRef,
  effect,
  ElementRef,
  inject,
  input,
  signal,
  untracked,
  viewChild,
} from '@angular/core';
import { Title } from '@angular/platform-browser';
import { takeUntilDestroyed } from '@angular/core/rxjs-interop';
import { Router, RouterLink, Scroll } from '@angular/router';
import { LucideArrowLeft, LucideArrowRight, LucideListTree } from '@lucide/angular';
import { filter } from 'rxjs';

import { ValiditySeal } from '../../../shared/ui/validity-seal/validity-seal';
import { RUNTIME_CONFIG } from '../../../core/config/runtime-config';
import { resolveApiUrl } from '../../../core/http/api-url';
import { OutlineEntry } from '../../../core/api/models';
import { entryLabel, isContainerKind, sentenceCase } from '../data-access/outline-labels';
import { ancestorsOf, neighbours } from '../data-access/outline-tree';
import { nodeLocator, provisionAnchor } from '../data-access/provision-labels';
import { ReaderStore } from '../data-access/reader.store';
import { ContainerView } from '../ui/container-view/container-view';
import { EditionHeader } from '../ui/edition-header/edition-header';
import { Folio } from '../ui/folio/folio';
import { OutlineTree } from '../ui/outline-tree/outline-tree';
import { HistorySelection, ProvisionNode } from '../ui/provision-node/provision-node';

type Pane = 'text' | 'pdf';

/**
 * Reader: index of a norm, the text of one provision with its history, notes and citations, and
 * the original PDF with the passage highlighted. The URL is the state (`/biblioteca/:norma?p=&v=`),
 * so every view can be shared and the browser's back button works.
 */
@Component({
  selector: 'drtc-reader-page',
  imports: [
    RouterLink,
    ContainerView,
    EditionHeader,
    Folio,
    OutlineTree,
    ProvisionNode,
    ValiditySeal,
    LucideArrowLeft,
    LucideArrowRight,
    LucideListTree,
  ],
  providers: [ReaderStore],
  templateUrl: './reader-page.html',
  styleUrl: './reader-page.css',
})
export class ReaderPage {
  /** Route parameter: id of the norm. */
  readonly norma = input.required<string>();
  /** Query parameter `p`: structural path to read ("articulo:2/literal:e"). */
  readonly p = input<string | undefined>();
  /** Query parameter `v`: edition (version id); omitted = the current approved edition. */
  readonly v = input<string | undefined>();

  protected readonly store = inject(ReaderStore);
  private readonly router = inject(Router);
  private readonly title = inject(Title);
  private readonly host = inject<ElementRef<HTMLElement>>(ElementRef);
  private readonly apiBaseUrl = inject(RUNTIME_CONFIG).apiBaseUrl;
  private readonly heading = viewChild<ElementRef<HTMLElement>>('heading');

  /** Small screens show one pane at a time. */
  protected readonly pane = signal<Pane>('text');
  protected readonly outlineOpen = signal(false);

  protected readonly pdfUrl = computed(() => {
    const edition = this.store.edition();
    return edition ? resolveApiUrl(edition.source_url, this.apiBaseUrl) : null;
  });

  protected readonly root = computed(() => this.store.unitTree()[0] ?? null);
  protected readonly isContainer = computed(() => {
    const root = this.root();
    return root !== null && isContainerKind(root.node.kind);
  });

  /** What the heading of the reading view says: "Artículo 2" + "De las definiciones". */
  protected readonly unitHeading = computed(() => {
    const root = this.root()?.node;
    if (!root) return null;
    if (isContainerKind(root.kind)) {
      const label = entryLabel({
        kind: root.kind,
        label: root.label,
        path: root.path,
        title: root.current.title,
      });
      return { locator: label.prefix, title: label.title };
    }
    const title = root.current.title ? sentenceCase(root.current.title) : null;
    return { locator: nodeLocator(root), title };
  });

  protected readonly currentEntry = computed(() => this.store.currentEntry());
  protected readonly ancestors = computed(() => {
    const current = this.currentEntry();
    return current ? ancestorsOf(this.store.entries(), current.path) : [];
  });
  /** Containers that hold the current entry, outermost first, as breadcrumb links. */
  protected readonly breadcrumb = computed(() => {
    const byPath = new Map(this.store.entries().map((e) => [e.path, e] as const));
    return [...this.ancestors()].reverse().flatMap((path) => {
      const entry = byPath.get(path);
      return entry ? [{ entry, label: entryLabel(entry) }] : [];
    });
  });
  protected readonly around = computed(() => {
    const { previous, next } = neighbours(this.store.entries(), this.store.focusPath());
    return {
      previous: previous && { entry: previous, label: entryLabel(previous) },
      next: next && { entry: next, label: entryLabel(next) },
    };
  });

  protected readonly route = computed(() => ['/biblioteca', this.norma()]);
  private readonly pageTitle = computed(() => {
    const heading = this.unitHeading();
    const norm = this.store.edition()?.short_name ?? this.norma();
    return [heading?.locator, norm, 'DRTC Puno'].filter(Boolean).join(' · ');
  });

  /** The unit last shown, to move focus to the heading only when the person changes provision. */
  private shownUnit: string | null = null;

  constructor() {
    // The URL decides what is open. `open` and `focus` are independent on purpose: a slow outline
    // must never delay or override the choice of provision.
    effect(() => {
      const norma = this.norma();
      const version = this.v() ?? null;
      const path = this.p() ?? null;
      untracked(() => {
        void this.store.open(norma, version);
        void this.store.focus(path);
      });
    });

    effect(() => this.title.setTitle(this.pageTitle()));

    // A new provision closes the index panel (small screens) and returns to the text.
    effect(() => {
      this.store.focusPath();
      untracked(() => this.outlineOpen.set(false));
    });

    afterRenderEffect(() => {
      const unit = this.store.unit();
      const status = this.store.unitStatus();
      this.store.focusPath();
      untracked(() => {
        if (!unit || status !== 'ready') return;
        if (this.shownUnit !== null && this.shownUnit !== unit.unit_path) {
          this.heading()?.nativeElement.focus({ preventScroll: true });
        }
        this.shownUnit = unit.unit_path;
        this.scrollToFocus();
      });
    });

    // The router scrolls to the top after every navigation; re-apply the scroll to the chosen
    // passage right after it, in the same task, so there is no visible jump.
    this.router.events
      .pipe(
        filter((event): event is Scroll => event instanceof Scroll),
        takeUntilDestroyed(inject(DestroyRef)),
      )
      .subscribe(() => this.scrollToFocus());
  }

  protected linkParams(entry: OutlineEntry): Record<string, string> {
    const version = this.v();
    return version ? { p: entry.path, v: version } : { p: entry.path };
  }

  /** "Ver en el PDF": highlight this passage; the URL keeps it so it can be shared. */
  protected viewPassage(path: string): void {
    void this.store.focus(path);
    this.pane.set('pdf');
    const version = this.v();
    void this.router.navigate(this.route(), {
      queryParams: version ? { p: path, v: version } : { p: path },
    });
  }

  protected viewHistory(selection: HistorySelection): void {
    this.store.showHistory(selection.path, selection.revision);
    this.pane.set('pdf');
  }

  protected showPane(pane: Pane): void {
    this.pane.set(pane);
  }

  protected toggleOutline(): void {
    this.outlineOpen.update((open) => !open);
  }

  protected retryOutline(): void {
    void this.store.retryOutline();
  }

  protected retryUnit(): void {
    void this.store.retryUnit();
  }

  private scrollToFocus(): void {
    const unit = this.store.unit();
    const focus = this.store.focusPath();
    if (!unit || !focus) return;
    if (focus === unit.unit_path) {
      // One pane at a time: skip the page header so the provision starts at the top of the screen.
      if (this.singlePane()) this.heading()?.nativeElement.scrollIntoView?.({ block: 'start' });
      return;
    }
    this.host.nativeElement
      .querySelector<HTMLElement>(`#${provisionAnchor(focus)}`)
      ?.scrollIntoView?.({ block: 'center' });
  }

  private singlePane(): boolean {
    return typeof matchMedia === 'function' && matchMedia('(max-width: 63.99rem)').matches;
  }
}
