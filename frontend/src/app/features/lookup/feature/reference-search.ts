import {
  Component,
  computed,
  effect,
  ElementRef,
  inject,
  signal,
  untracked,
  viewChild,
} from '@angular/core';
import { Router } from '@angular/router';
import { LucideSearch, LucideX } from '@lucide/angular';

import { LookupHit } from '../../../core/api/models';
import { LookupStore, MAX_QUERY_LENGTH } from '../data-access/lookup.store';

let nextId = 0;

/**
 * Search by reference ("art. 5 Ley 27181", "lit. e del art. 2", "anexo 2 RENAT"). It finds a place
 * in a norm, it does not answer questions: when the text is ambiguous it lists the candidates and
 * the person chooses. Combobox pattern (ARIA 1.2): focus stays in the field, the arrows move
 * through the results with `aria-activedescendant`.
 */
@Component({
  selector: 'drtc-reference-search',
  imports: [LucideSearch, LucideX],
  providers: [LookupStore],
  templateUrl: './reference-search.html',
  styleUrl: './reference-search.css',
  host: {
    '(document:keydown)': 'onDocumentKeydown($event)',
    '(focusout)': 'onFocusOut($event)',
  },
})
export class ReferenceSearch {
  protected readonly store = inject(LookupStore);
  private readonly router = inject(Router);
  private readonly host = inject<ElementRef<HTMLElement>>(ElementRef);
  private readonly field = viewChild.required<ElementRef<HTMLInputElement>>('field');

  protected readonly uid = `busqueda-${nextId++}`;
  protected readonly maxLength = MAX_QUERY_LENGTH;
  private readonly focused = signal(false);
  private readonly dismissed = signal(false);
  /** Enter was pressed before there was a result: open the answer if it turns out to be unique. */
  private goWhenResolved = false;

  protected readonly isOpen = computed(
    () => this.focused() && !this.dismissed() && this.store.status() !== 'idle',
  );
  /** The listbox always has the final «search in the text» option while there is text to search. */
  protected readonly showList = computed(() => this.isOpen() && this.store.query().trim() !== '');
  /** Index of the «search in the text» option: right after the last result. */
  protected readonly textOptionIndex = computed(() => this.store.hits().length);
  protected readonly textOptionActive = computed(
    () => this.showList() && this.store.activeIndex() === this.textOptionIndex(),
  );
  protected readonly activeId = computed(() => {
    const index = this.store.activeIndex();
    return this.showList() && index >= 0 ? `${this.uid}-op-${index}` : null;
  });

  /** One sentence for the person (and the screen reader) about what the search understood. */
  protected readonly statusText = computed(() => {
    switch (this.store.status()) {
      case 'loading':
        return 'Buscando…';
      case 'error':
        return this.store.error() ?? '';
      case 'done': {
        const result = this.store.result();
        if (!result) return '';
        if (result.message) return result.message;
        const count = result.hits.length;
        return count === 1 ? '1 resultado.' : `${count} resultados.`;
      }
      default:
        return '';
    }
  });

  constructor() {
    effect(() => {
      const result = this.store.result();
      if (!result || !untracked(() => this.goWhenResolved)) return;
      this.goWhenResolved = false;
      const [only] = result.hits;
      if (result.status === 'resolved' && result.hits.length === 1 && only) this.open(only);
      // Not a reference at all: the person wants to search the text, so take them there.
      else if (result.status === 'unrecognized') this.searchText();
    });
  }

  protected onInput(event: Event): void {
    this.goWhenResolved = false;
    this.dismissed.set(false);
    this.store.setQuery((event.target as HTMLInputElement).value);
  }

  protected onKeydown(event: KeyboardEvent): void {
    switch (event.key) {
      case 'ArrowDown':
      case 'ArrowUp':
        if (!this.store.query().trim()) return;
        event.preventDefault();
        this.dismissed.set(false);
        this.store.moveActive(event.key === 'ArrowDown' ? 1 : -1, 1);
        return;
      case 'Enter': {
        event.preventDefault();
        const active = this.showList() ? this.store.activeHit() : null;
        if (this.textOptionActive()) {
          this.searchText();
        } else if (active) {
          this.open(active);
        } else if (this.store.query().trim()) {
          this.dismissed.set(false);
          this.goWhenResolved = true;
          this.store.submit();
        }
        return;
      }
      case 'Escape':
        if (this.isOpen()) {
          event.preventDefault();
          this.dismissed.set(true);
        } else if (this.store.query()) {
          event.preventDefault();
          this.clear();
        }
        return;
    }
  }

  protected onFocusIn(): void {
    this.focused.set(true);
  }

  protected onFocusOut(event: FocusEvent): void {
    const next = event.relatedTarget as Node | null;
    if (!next || !this.host.nativeElement.contains(next)) this.focused.set(false);
  }

  protected clear(): void {
    this.goWhenResolved = false;
    this.store.clear();
    this.field().nativeElement.focus();
  }

  /** Go to the place found, in the edition where it was found. */
  protected open(hit: LookupHit): void {
    const queryParams: Record<string, string> = {};
    if (hit.path) queryParams['p'] = hit.path;
    if (hit.version_id) queryParams['v'] = hit.version_id;
    void this.router.navigate(['/biblioteca', hit.instrument_id], { queryParams });
    this.goWhenResolved = false;
    this.store.clear();
    this.dismissed.set(true);
    this.field().nativeElement.blur();
  }

  /**
   * Search the CONTENT of the norms for what was typed. Only here — on Enter or a click — does the
   * text leave the box towards /search: typing alone only ever asks /lookup (local and free).
   */
  protected searchText(): void {
    const q = this.store.query().trim();
    if (!q) return;
    void this.router.navigate(['/buscar'], { queryParams: { q } });
    this.goWhenResolved = false;
    this.store.clear();
    this.dismissed.set(true);
    this.field().nativeElement.blur();
  }

  protected isUnverified(hit: LookupHit): boolean {
    return hit.verification_status !== 'verified_current';
  }

  protected pageLabel(hit: LookupHit): string {
    return hit.page_start ? `p. ${hit.page_start}` : '';
  }

  /** "/" jumps to the search from anywhere, like in most documentation sites. */
  protected onDocumentKeydown(event: KeyboardEvent): void {
    if (event.key !== '/' || event.ctrlKey || event.metaKey || event.altKey) return;
    const target = event.target as HTMLElement | null;
    if (
      target?.closest('input, textarea, select, [contenteditable=""], [contenteditable="true"]')
    ) {
      return;
    }
    event.preventDefault();
    this.field().nativeElement.focus();
  }
}
