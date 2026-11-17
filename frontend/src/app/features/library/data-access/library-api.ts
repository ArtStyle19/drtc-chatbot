import { HttpClient } from '@angular/common/http';
import { inject, Service } from '@angular/core';
import { map, Observable } from 'rxjs';

import { LegalInstrument, LegalInstrumentList } from '../../../core/api/models';

/** HTTP adapter of the Biblioteca feature (contract: backend/openapi.json). */
@Service()
export class LibraryApi {
  private readonly http = inject(HttpClient);

  listInstruments(): Observable<readonly LegalInstrument[]> {
    return this.http
      .get<LegalInstrumentList>('/api/v1/instruments')
      .pipe(map((response) => response.items));
  }
}
