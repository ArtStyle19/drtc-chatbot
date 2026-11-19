import { computed, inject } from '@angular/core';
import { patchState, signalStore, withComputed, withMethods, withState } from '@ngrx/signals';
import { rxMethod } from '@ngrx/signals/rxjs-interop';
import { catchError, EMPTY, pipe, switchMap, tap } from 'rxjs';

import { SearchResponse } from '../../../core/api/models';
import { toUserMessage } from '../../../core/http/problem-details';
import { SearchApi, SearchParams } from './search-api';

/** The server's own limit for a text (backend MAX_QUERY_CHARS). */
export const MAX_SEARCH_LENGTH = 300;
export const SEARCH_PAGE_SIZE = 20;

type Status = 'idle' | 'loading' | 'done' | 'error';

interface SearchState {
  /** What the person asked for (the answer's own `query` may be normalised by the server). */
  readonly asked: { readonly query: string; readonly instrument: string | null } | null;
  readonly status: Status;
  readonly response: SearchResponse | null;
  readonly error: string | null;
}

const initialState: SearchState = { asked: null, status: 'idle', response: null, error: null };

/**
 * State of the «Buscar en el texto» page. Each call replaces the one in flight (switchMap
 * unsubscribes, which aborts the HTTP request), so a slow answer can never overwrite a newer one.
 * Changing only the norm filter keeps the list on screen (dimmed) instead of flashing a skeleton.
 */
export const SearchStore = signalStore(
  withState(initialState),
  withComputed((store) => ({
    results: computed(() => store.response()?.results ?? []),
    facets: computed(() => store.response()?.facets ?? []),
    degraded: computed(() => store.response()?.degraded ?? []),
    isLoading: computed(() => store.status() === 'loading'),
    /** The first answer for this text has not arrived: show a skeleton, not an empty state. */
    isFirstLoad: computed(() => store.status() === 'loading' && store.response() === null),
    isEmpty: computed(
      () => store.status() === 'done' && (store.response()?.results.length ?? 0) === 0,
    ),
  })),
  withMethods((store, api = inject(SearchApi)) => {
    const run = rxMethod<SearchParams>(
      pipe(
        switchMap((params) => {
          const keepList = store.asked()?.query === params.query && store.response() !== null;
          patchState(store, {
            asked: { query: params.query, instrument: params.instrument },
            status: 'loading',
            error: null,
            response: keepList ? store.response() : null,
          });
          return api.search(params).pipe(
            tap((response) => patchState(store, { status: 'done', response, error: null })),
            catchError((error: unknown) => {
              patchState(store, { status: 'error', response: null, error: toUserMessage(error) });
              return EMPTY;
            }),
          );
        }),
      ),
    );

    return {
      /** Search for `query` (optionally in one norm). An empty text clears the page. */
      search(query: string, instrument: string | null = null, debug = false): void {
        const text = query.trim().slice(0, MAX_SEARCH_LENGTH);
        if (!text) {
          patchState(store, initialState);
          return;
        }
        run({ query: text, instrument, limit: SEARCH_PAGE_SIZE, debug });
      },
      /** Ask again exactly what was asked (the «Reintentar» button). */
      retry(debug = false): void {
        const asked = store.asked();
        if (asked) run({ ...asked, limit: SEARCH_PAGE_SIZE, debug });
      },
    };
  }),
);
