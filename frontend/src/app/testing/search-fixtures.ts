import { SearchResponse, SearchResult } from '../core/api/models';

/** A search result as the API returns it (shape of GET /api/v1/search). */
export function searchResult(overrides: Partial<SearchResult> = {}): SearchResult {
  return {
    instrument_id: 'ley-27181',
    instrument_short_name: 'Ley 27181 (LGTTT)',
    version_id: 'ley-27181@2020-05',
    edition_label: 'Compilación no oficial hasta mayo de 2020',
    verification_status: 'unverified',
    may_be_presented_as_current: false,
    unit_path: 'articulo:2',
    path: 'articulo:2/literal:e',
    kind: 'literal',
    label: 'e',
    title: 'Definiciones',
    citation: 'Ley N.° 27181, art. 2, lit. e)',
    page_start: 3,
    page_end: 3,
    snippet: [
      { text: 'Servicio de ', match: false },
      { text: 'transporte', match: true },
      { text: ' de personas.', match: false },
    ],
    matched: [
      {
        path: 'articulo:2/literal:e',
        citation: 'Ley N.° 27181, art. 2, lit. e)',
        page_start: 3,
        page_end: 3,
        snippet: [{ text: 'Servicio de transporte', match: false }],
      },
    ],
    via: ['lexical'],
    score: 0.03,
    debug: null,
    ...overrides,
  };
}

export function searchResponse(overrides: Partial<SearchResponse> = {}): SearchResponse {
  return {
    query: 'transporte de personas',
    mode: 'hybrid',
    degraded: [],
    total: 1,
    reference: null,
    facets: [
      { instrument_id: 'ley-27181', short_name: 'Ley 27181 (LGTTT)', count: 3 },
      { instrument_id: 'ds-017-2009-mtc', short_name: 'RENAT (DS 017-2009-MTC)', count: 2 },
    ],
    results: [searchResult()],
    ...overrides,
  };
}
