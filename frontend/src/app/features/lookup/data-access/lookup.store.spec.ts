import { HttpErrorResponse } from '@angular/common/http';
import { TestBed } from '@angular/core/testing';
import { Observable, of, Subject, throwError } from 'rxjs';

import { LookupHit, LookupResult } from '../../../core/api/models';
import { LookupApi } from './lookup-api';
import { LOOKUP_DEBOUNCE_MS, LookupStore } from './lookup.store';

function hit(path: string): LookupHit {
  return {
    instrument_id: 'ley-27181',
    instrument_short_name: 'Ley 27181 (LGTTT)',
    instrument_title: 'Ley General',
    citation: `Ley N.° 27181, ${path}`,
    version_id: 'ley-27181@2020-05',
    edition_label: 'Edición',
    verification_status: 'unverified',
    path,
    unit_path: path,
    kind: 'article',
    label: '5',
    title: null,
    snippet: 'Texto',
    page_start: 5,
  };
}

function result(status: LookupResult['status'], hits: LookupHit[] = []): LookupResult {
  return {
    status,
    query: 'q',
    message: '',
    reference: 'art. 5',
    norms: [],
    total: hits.length,
    hits,
    ignored_text: null,
  };
}

class FakeApi {
  queries: string[] = [];
  respond: (q: string) => Observable<LookupResult> = () =>
    of(result('resolved', [hit('articulo:5')]));
  lookup(q: string): Observable<LookupResult> {
    this.queries.push(q);
    return this.respond(q);
  }
}

function setup(api = new FakeApi()) {
  TestBed.configureTestingModule({
    providers: [LookupStore, { provide: LookupApi, useValue: api }],
  });
  return { store: TestBed.inject(LookupStore), api };
}

describe('LookupStore', () => {
  beforeEach(() => vi.useFakeTimers());
  afterEach(() => vi.useRealTimers());

  it('waits for the person to stop typing and sends only the last text', async () => {
    const { store, api } = setup();

    store.setQuery('art');
    store.setQuery('art 5');
    store.setQuery('art 5 ley 27181');
    await vi.advanceTimersByTimeAsync(LOOKUP_DEBOUNCE_MS - 1);
    expect(api.queries).toEqual([]);
    await vi.advanceTimersByTimeAsync(1);

    expect(api.queries).toEqual(['art 5 ley 27181']);
    expect(store.status()).toBe('done');
    expect(store.hits()).toHaveLength(1);
    expect(store.activeHit()?.path).toBe('articulo:5'); // a single result is already active
  });

  it('searches at once on submit', async () => {
    const { store, api } = setup();

    store.setQuery('art 5');
    store.submit();
    await vi.advanceTimersByTimeAsync(0);

    expect(api.queries).toEqual(['art 5']);
  });

  it('keeps no active result when there are several, and cycles with the arrows', async () => {
    const api = new FakeApi();
    api.respond = () =>
      of(result('ambiguous', [hit('articulo:5'), hit('articulo:6'), hit('articulo:7')]));
    const { store } = setup(api);

    store.setQuery('art');
    await vi.advanceTimersByTimeAsync(LOOKUP_DEBOUNCE_MS);
    expect(store.activeIndex()).toBe(-1);

    store.moveActive(1);
    store.moveActive(1);
    expect(store.activeHit()?.path).toBe('articulo:6');
    store.moveActive(-1);
    store.moveActive(-1);
    expect(store.activeHit()?.path).toBe('articulo:7'); // wraps around
  });

  it('ignores the answer of an older query', async () => {
    const api = new FakeApi();
    const slow = new Subject<LookupResult>();
    api.respond = (q) => (q === 'old' ? slow : of(result('resolved', [hit('articulo:6')])));
    const { store } = setup(api);

    store.setQuery('old');
    await vi.advanceTimersByTimeAsync(LOOKUP_DEBOUNCE_MS);
    store.setQuery('new');
    await vi.advanceTimersByTimeAsync(LOOKUP_DEBOUNCE_MS);
    slow.next(result('resolved', [hit('articulo:5')]));
    await vi.advanceTimersByTimeAsync(0);

    expect(store.activeHit()?.path).toBe('articulo:6');
  });

  it('returns to idle for an empty text and never calls the API', async () => {
    const { store, api } = setup();

    store.setQuery('   ');
    await vi.advanceTimersByTimeAsync(LOOKUP_DEBOUNCE_MS);

    expect(store.status()).toBe('idle');
    expect(api.queries).toEqual([]);
  });

  it('explains a failure in Spanish and keeps the typed text', async () => {
    const api = new FakeApi();
    api.respond = () => throwError(() => new HttpErrorResponse({ status: 0 }));
    const { store } = setup(api);

    store.setQuery('art 5');
    await vi.advanceTimersByTimeAsync(LOOKUP_DEBOUNCE_MS);

    expect(store.status()).toBe('error');
    expect(store.error()).toContain('No se pudo conectar');
    expect(store.query()).toBe('art 5');
  });

  it('can be cleared', async () => {
    const { store } = setup();
    store.setQuery('art 5');
    await vi.advanceTimersByTimeAsync(LOOKUP_DEBOUNCE_MS);

    store.clear();

    expect(store.query()).toBe('');
    expect(store.result()).toBeNull();
  });
});
