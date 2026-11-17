import { HttpErrorResponse } from '@angular/common/http';
import { TestBed } from '@angular/core/testing';
import { Observable, of, throwError } from 'rxjs';

import { LegalInstrument } from '../../../core/api/models';
import { anInstrument } from '../../../testing/instrument-fixtures';
import { LibraryApi } from './library-api';
import { LibraryStore } from './library.store';

function setup(response: () => Observable<readonly LegalInstrument[]>) {
  TestBed.configureTestingModule({
    providers: [LibraryStore, { provide: LibraryApi, useValue: { listInstruments: response } }],
  });
  return TestBed.inject(LibraryStore);
}

describe('LibraryStore', () => {
  it('loads the instruments when created', async () => {
    const store = setup(() => of([anInstrument(), anInstrument({ id: 'ds-017-2009-mtc' })]));
    await store.load();

    expect(store.status()).toBe('loaded');
    expect(store.instruments().map((item) => item.id)).toEqual(['ley-27181', 'ds-017-2009-mtc']);
    expect(store.unverifiedCount()).toBe(2);
  });

  it('exposes a user-facing message when the API fails', async () => {
    const store = setup(() => throwError(() => new HttpErrorResponse({ status: 0 })));
    await store.load();

    expect(store.status()).toBe('error');
    expect(store.errorMessage()).toContain('No se pudo conectar con el servidor');
  });

  it('reports an empty corpus', async () => {
    const store = setup(() => of([]));
    await store.load();

    expect(store.isEmpty()).toBe(true);
  });
});
