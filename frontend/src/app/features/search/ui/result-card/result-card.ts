import { Component, computed, input } from '@angular/core';
import { RouterLink } from '@angular/router';

import { SearchMatchedPassage, SearchResult, SearchVia } from '../../../../core/api/models';
import { ValiditySeal } from '../../../../shared/ui/validity-seal/validity-seal';
import { sealStatus } from '../../../../shared/util/verification';
import { Snippet } from '../snippet/snippet';

let nextId = 0;

const VIA_LABELS: Record<SearchVia, string> = {
  reference: 'Referencia exacta',
  lexical: 'Por palabras',
  vector: 'Por significado',
};

/** Pages as a person writes them: "p. 12" or "pp. 12–13". */
export function pageLabel(start: number, end: number): string {
  return start === end ? `p. ${start}` : `pp. ${start}–${end}`;
}

/**
 * One reading unit found by the search: the server's citation, where it is, how sure we are that
 * it is in force (the seal), the matching words in context and a link to read it in the norm.
 * It shows what was FOUND; it never rephrases or concludes anything.
 */
@Component({
  selector: 'drtc-result-card',
  imports: [RouterLink, Snippet, ValiditySeal],
  templateUrl: './result-card.html',
  styleUrl: './result-card.css',
})
export class ResultCard {
  readonly result = input.required<SearchResult>();
  /** Show the diagnostic panel (which method found it and how it ranked). */
  readonly diagnostics = input(false);

  protected readonly uid = `resultado-${nextId++}`;

  protected readonly seal = computed(() =>
    sealStatus(this.result().verification_status, this.result().may_be_presented_as_current),
  );
  protected readonly pages = computed(() =>
    pageLabel(this.result().page_start, this.result().page_end),
  );
  protected readonly vias = computed(() => this.result().via.map((via) => VIA_LABELS[via]));
  protected readonly isExactReference = computed(() => this.result().via.includes('reference'));

  /** The other passages of the same unit that matched (the first one is the snippet above). */
  protected readonly others = computed(() => this.result().matched.slice(1));

  protected readonly debugEntries = computed(() =>
    Object.entries(this.result().debug ?? {}).map(
      ([key, value]) => [key, typeof value === 'string' ? value : JSON.stringify(value)] as const,
    ),
  );

  protected readonly readLink = computed(() => ['/biblioteca', this.result().instrument_id]);
  protected readonly readParams = computed(() => this.paramsFor(this.result().path));

  protected paramsFor(path: string): Record<string, string> {
    return { p: path, v: this.result().version_id };
  }

  protected otherPages(passage: SearchMatchedPassage): string {
    return pageLabel(passage.page_start, passage.page_end);
  }
}
