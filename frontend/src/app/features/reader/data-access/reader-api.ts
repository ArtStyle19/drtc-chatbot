import { HttpClient, HttpParams } from '@angular/common/http';
import { inject, Service } from '@angular/core';
import { Observable } from 'rxjs';

import { Outline, ReadingUnit } from '../../../core/api/models';

/** HTTP adapter of the reader (contract: backend/openapi.json). */
@Service()
export class ReaderApi {
  private readonly http = inject(HttpClient);

  outline(instrumentId: string, versionId: string | null): Observable<Outline> {
    return this.http.get<Outline>(
      `/api/v1/instruments/${encodeURIComponent(instrumentId)}/outline`,
      {
        params: this.versionParams(versionId),
      },
    );
  }

  readingUnit(
    instrumentId: string,
    path: string,
    versionId: string | null,
  ): Observable<ReadingUnit> {
    return this.http.get<ReadingUnit>(
      `/api/v1/instruments/${encodeURIComponent(instrumentId)}/reading-unit`,
      {
        params: this.versionParams(versionId).set('path', path),
      },
    );
  }

  private versionParams(versionId: string | null): HttpParams {
    return versionId ? new HttpParams().set('version_id', versionId) : new HttpParams();
  }
}
