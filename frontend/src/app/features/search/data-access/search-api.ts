import { HttpClient, HttpParams } from '@angular/common/http';
import { inject, Service } from '@angular/core';
import { Observable } from 'rxjs';

import { SearchResponse } from '../../../core/api/models';

export interface SearchParams {
  readonly query: string;
  /** Limit the search to one norm (id). */
  readonly instrument: string | null;
  readonly limit: number;
  /** Ask for the diagnostic view; the server only honours it in development and test. */
  readonly debug: boolean;
}

/** HTTP adapter of the content search (GET /api/v1/search). */
@Service()
export class SearchApi {
  private readonly http = inject(HttpClient);

  search({ query, instrument, limit, debug }: SearchParams): Observable<SearchResponse> {
    let params = new HttpParams().set('q', query).set('limit', limit);
    if (instrument) params = params.set('instrument', instrument);
    if (debug) params = params.set('debug', true);
    return this.http.get<SearchResponse>('/api/v1/search', { params });
  }
}
