import {
  Component,
  computed,
  effect,
  ElementRef,
  inject,
  isDevMode,
  untracked,
  viewChild,
} from '@angular/core';
import { toSignal } from '@angular/core/rxjs-interop';
import { Title } from '@angular/platform-browser';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { LucideSearch } from '@lucide/angular';

import { SearchDegradedReason } from '../../../core/api/models';
import { MAX_SEARCH_LENGTH, SearchStore } from '../data-access/search.store';
import { ResultCard } from '../ui/result-card/result-card';

const DEGRADED_MESSAGES: Record<SearchDegradedReason, string> = {
  vector_unavailable:
    'La búsqueda por significado no está disponible ahora: se muestran solo las coincidencias por palabras. Puede que falten resultados que usan otros términos.',
  vector_not_indexed:
    'La búsqueda por significado aún no se ha preparado en este entorno: se muestran solo las coincidencias por palabras.',
};

const EXAMPLES: readonly string[] = [
  'plazo para interponer recurso de apelación',
  'silencio administrativo positivo',
  'servicio de mototaxi',
];

/**
 * «Buscar en el texto»: finds provisions by what they say, with the person's own words. The URL
 * (`/buscar?q=&norma=`) is the single source of truth: typing never searches, submitting changes
 * the URL and the URL drives the search, so the page can be shared, reloaded and gone back to.
 * It lists matches with their source; it does not answer the question.
 */
@Component({
  selector: 'drtc-search-page',
  imports: [ResultCard, LucideSearch, RouterLink],
  providers: [SearchStore],
  templateUrl: './search-page.html',
  styleUrl: './search-page.css',
})
export class SearchPage {
  protected readonly store = inject(SearchStore);
  private readonly route = inject(ActivatedRoute);
  private readonly router = inject(Router);
  private readonly title = inject(Title);
  private readonly field = viewChild.required<ElementRef<HTMLInputElement>>('field');

  protected readonly maxLength = MAX_SEARCH_LENGTH;
  protected readonly examples = EXAMPLES;
  /** The diagnostic view is a developer's tool: the server ignores it outside local/test. */
  protected readonly diagnosticsAvailable = isDevMode();

  private readonly params = toSignal(this.route.queryParamMap, { requireSync: true });
  protected readonly query = computed(() => (this.params().get('q') ?? '').trim());
  protected readonly norm = computed(() => this.params().get('norma'));
  protected readonly diagnostics = computed(
    () => this.diagnosticsAvailable && this.params().get('debug') === '1',
  );

  protected readonly facets = this.store.facets;
  protected readonly degradedMessages = computed(() =>
    this.store.degraded().map((reason) => DEGRADED_MESSAGES[reason]),
  );
  protected readonly activeNormName = computed(
    () => this.facets().find((facet) => facet.instrument_id === this.norm())?.short_name ?? null,
  );

  protected readonly count = computed(() => {
    const response = this.store.response();
    if (!response) return '';
    const shown = response.results.length;
    if (shown === 0) return 'Sin resultados.';
    const noun = (n: number) => (n === 1 ? '1 resultado' : `${n} resultados`);
    return response.total > shown
      ? `Se muestran ${shown} de ${response.total} resultados.`
      : `${noun(shown)}.`;
  });

  protected readonly emptyMessage = computed(() => {
    const where = this.activeNormName();
    return `No encontramos coincidencias para «${this.query()}»${where ? ` en ${where}` : ''}.`;
  });

  protected readonly referenceNote = computed(() => {
    const response = this.store.response();
    const first = response?.results[0];
    if (!response?.reference || !first?.via.includes('reference')) return null;
    return `Se entendió «${response.reference}» como una referencia exacta: va primero.`;
  });

  constructor() {
    effect(() => {
      const query = this.query();
      const norm = this.norm();
      const diagnostics = this.diagnostics();
      untracked(() => this.store.search(query, norm, diagnostics));
      this.title.setTitle(
        query ? `Buscar «${query}» · DRTC Puno` : 'Buscar en el texto · DRTC Puno',
      );
    });
  }

  /** A new text is a new search: the norm filter is dropped, it would hide most of what is new. */
  protected submit(event: Event): void {
    event.preventDefault();
    const text = this.field().nativeElement.value.trim();
    if (!text) {
      this.field().nativeElement.focus();
      return;
    }
    void this.router.navigate(['/buscar'], {
      queryParams: { q: text, debug: this.diagnostics() ? '1' : null },
    });
  }

  protected filterBy(instrumentId: string | null): void {
    void this.router.navigate(['/buscar'], {
      queryParams: { q: this.query(), norma: instrumentId, debug: this.diagnostics() ? '1' : null },
    });
  }

  protected toggleDiagnostics(): void {
    void this.router.navigate(['/buscar'], {
      queryParams: { debug: this.diagnostics() ? null : '1' },
      queryParamsHandling: 'merge',
    });
  }

  protected retry(): void {
    this.store.retry(this.diagnostics());
  }

  protected exampleParams(example: string): Record<string, string> {
    return { q: example };
  }
}
