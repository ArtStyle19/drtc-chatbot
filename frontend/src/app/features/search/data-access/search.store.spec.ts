import { HttpErrorResponse } from '@angular/common/http';
import { TestBed } from '@angular/core/testing';
import { Observable, of, Subject, throwError } from 'rxjs';

import { SearchResponse } from '../../../core/api/models';
import { searchResponse, searchResult } from '../../../testing/search-fixtures';
import { SearchApi, SearchParams } from './search-api';
import { MAX_SEARCH_LENGTH, SEARCH_PAGE_SIZE, SearchStore } from './search.store';

class FakeApi {
  calls: SearchParams[] = [];
  respond: (params: SearchParams) => Observable<SearchResponse> = () => of(searchResponse());
  search(params: SearchParams): Observable<SearchResponse> {
    this.calls.push(params);
    return this.respond(params);
  }
}

function setup(api = new FakeApi()) {
  TestBed.configureTestingModule({
    providers: [SearchStore, { provide: SearchApi, useValue: api }],
  });
  return { store: TestBed.inject(SearchStore), api };
}

describe('SearchStore', () => {
  it('starts idle and does not search by itself', () => {
    const { store, api } = setup();

    expect(store.status()).toBe('idle');
    expect(store.results()).toEqual([]);
    expect(api.calls).toEqual([]);
  });

  it('asks for the trimmed text, a page of results and no diagnostics by default', () => {
    const { store, api } = setup();

    store.search('  plazo para apelar  ');

    expect(api.calls).toEqual([
      { query: 'plazo para apelar', instrument: null, limit: SEARCH_PAGE_SIZE, debug: false },
    ]);
    expect(store.status()).toBe('done');
    expect(store.results()).toHaveLength(1);
  });

  it('never sends more than the server accepts', () => {
    const { store, api } = setup();

    store.search('x'.repeat(MAX_SEARCH_LENGTH + 50));

    expect(api.calls[0]?.query).toHaveLength(MAX_SEARCH_LENGTH);
  });

  it('passes the norm filter and the diagnostics flag on', () => {
    const { store, api } = setup();

    store.search('multa', 'ds-017-2009-mtc', true);

    expect(api.calls[0]).toMatchObject({ instrument: 'ds-017-2009-mtc', debug: true });
  });

  it('does not call the server for an empty text and clears what was shown', () => {
    const { store, api } = setup();
    store.search('multa');

    store.search('   ');

    expect(api.calls).toHaveLength(1);
    expect(store.status()).toBe('idle');
    expect(store.response()).toBeNull();
  });

  it('exposes the degraded reasons and the facets of the answer', () => {
    const api = new FakeApi();
    api.respond = () => of(searchResponse({ degraded: ['vector_unavailable'] }));
    const { store } = setup(api);

    store.search('multa');

    expect(store.degraded()).toEqual(['vector_unavailable']);
    expect(store.facets().map((f) => f.instrument_id)).toEqual(['ley-27181', 'ds-017-2009-mtc']);
  });

  it('says it is empty only after an answer without results', () => {
    const api = new FakeApi();
    api.respond = () => of(searchResponse({ total: 0, results: [] }));
    const { store } = setup(api);
    expect(store.isEmpty()).toBe(false);

    store.search('asdfgh');

    expect(store.isEmpty()).toBe(true);
  });

  describe('a slow answer never overwrites a newer one', () => {
    it('keeps the newest answer even if the older one arrives last', () => {
      const first = new Subject<SearchResponse>();
      const second = new Subject<SearchResponse>();
      const api = new FakeApi();
      api.respond = ({ query }) => (query === 'primero' ? first : second);
      const { store } = setup(api);

      store.search('primero');
      store.search('segundo');
      second.next(searchResponse({ query: 'segundo', results: [searchResult({ label: 'S' })] }));
      first.next(searchResponse({ query: 'primero', results: [searchResult({ label: 'P' })] }));

      expect(store.response()?.query).toBe('segundo');
      expect(store.results().map((r) => r.label)).toEqual(['S']);
      expect(first.observed).toBe(false); // its request was cancelled, not just ignored
    });

    it('ignores an error of a request that was already replaced', () => {
      const first = new Subject<SearchResponse>();
      const api = new FakeApi();
      api.respond = ({ query }) => (query === 'primero' ? first : of(searchResponse()));
      const { store } = setup(api);

      store.search('primero');
      store.search('segundo');
      first.error(new HttpErrorResponse({ status: 500 }));

      expect(store.status()).toBe('done');
      expect(store.error()).toBeNull();
    });
  });

  describe('while loading', () => {
    it('shows a skeleton for a new text (nothing to keep) ...', () => {
      const pending = new Subject<SearchResponse>();
      const api = new FakeApi();
      api.respond = () => pending;
      const { store } = setup(api);

      store.search('multa');

      expect(store.isFirstLoad()).toBe(true);
      expect(store.isLoading()).toBe(true);
    });

    it('... but keeps the list on screen when only the norm filter changes', () => {
      const api = new FakeApi();
      const { store } = setup(api);
      store.search('multa');
      const pending = new Subject<SearchResponse>();
      api.respond = () => pending;

      store.search('multa', 'ley-27181');

      expect(store.status()).toBe('loading');
      expect(store.isFirstLoad()).toBe(false);
      expect(store.results()).toHaveLength(1);
    });

    it('drops the old list when the text changes', () => {
      const api = new FakeApi();
      const { store } = setup(api);
      store.search('multa');
      api.respond = () => new Subject<SearchResponse>();

      store.search('licencia');

      expect(store.isFirstLoad()).toBe(true);
      expect(store.results()).toEqual([]);
    });
  });

  describe('errors', () => {
    it('shows a message for people, never the technical detail', () => {
      const api = new FakeApi();
      api.respond = () =>
        throwError(
          () =>
            new HttpErrorResponse({
              status: 500,
              error: { code: 'internal_error_xyz', detail: 'Traceback (most recent call last)' },
            }),
        );
      const { store } = setup(api);

      store.search('multa');

      expect(store.status()).toBe('error');
      expect(store.error()).toContain('El servidor tuvo un problema');
      expect(store.error()).not.toContain('Traceback');
      expect(store.results()).toEqual([]);
    });

    it('retries exactly what was asked, norm included', () => {
      const api = new FakeApi();
      api.respond = () => throwError(() => new HttpErrorResponse({ status: 0 }));
      const { store } = setup(api);
      store.search('multa', 'tuo-ley-27444');
      api.respond = () => of(searchResponse());

      store.retry();

      expect(api.calls.at(-1)).toEqual({
        query: 'multa',
        instrument: 'tuo-ley-27444',
        limit: SEARCH_PAGE_SIZE,
        debug: false,
      });
      expect(store.status()).toBe('done');
      expect(store.error()).toBeNull();
    });

    it('does nothing when asked to retry before anything was searched', () => {
      const { store, api } = setup();

      store.retry();

      expect(api.calls).toEqual([]);
    });
  });
});
