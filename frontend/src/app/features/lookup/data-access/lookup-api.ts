import { HttpClient, HttpParams } from '@angular/common/http';
import { inject, Service } from '@angular/core';
import { Observable } from 'rxjs';

import { LookupResult } from '../../../core/api/models';

/** HTTP adapter of the reference search (GET /api/v1/lookup). */
@Service()
export class LookupApi {
  private readonly http = inject(HttpClient);

  lookup(query: string): Observable<LookupResult> {
    return this.http.get<LookupResult>('/api/v1/lookup', {
      params: new HttpParams().set('q', query),
    });
  }
}
