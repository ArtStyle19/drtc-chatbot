import { computed, inject } from '@angular/core';
import { patchState, signalStore, withComputed, withMethods, withState } from '@ngrx/signals';
import { rxMethod } from '@ngrx/signals/rxjs-interop';
import { catchError, EMPTY, pipe, switchMap, tap, timer } from 'rxjs';

import { LookupResult } from '../../../core/api/models';
import { toUserMessage } from '../../../core/http/problem-details';
import { LookupApi } from './lookup-api';

export const LOOKUP_DEBOUNCE_MS = 250;
export const MAX_QUERY_LENGTH = 300;

interface LookupState {
  readonly query: string;
  readonly status: 'idle' | 'loading' | 'done' | 'error';
  readonly result: LookupResult | null;
  readonly error: string | null;
  readonly activeIndex: number;
}

const initialState: LookupState = {
  query: '',
  status: 'idle',
  result: null,
  error: null,
  activeIndex: -1,
};

interface Request {
  readonly query: string;
  readonly immediate: boolean;
}

/**
 * State of the reference search. Typing is debounced; Enter searches right away. A newer request
 * cancels the one in flight (switchMap), so a slow answer can never replace a newer one.
 */
export const LookupStore = signalStore(
  withState(initialState),
  withComputed((store) => ({
    hits: computed(() => store.result()?.hits ?? []),
    activeHit: computed(() => store.result()?.hits[store.activeIndex()] ?? null),
    hasResults: computed(() => (store.result()?.hits.length ?? 0) > 0),
  })),
  withMethods((store, api = inject(LookupApi)) => {
    const run = rxMethod<Request>(
      pipe(
        switchMap(({ query, immediate }) => {
          const text = query.trim();
          if (!text) {
            patchState(store, { status: 'idle', result: null, error: null, activeIndex: -1 });
            return EMPTY;
          }
          patchState(store, { status: 'loading', error: null });
          return timer(immediate ? 0 : LOOKUP_DEBOUNCE_MS).pipe(
            switchMap(() => api.lookup(text.slice(0, MAX_QUERY_LENGTH))),
            tap((result) =>
              patchState(store, {
                status: 'done',
                result,
                error: null,
                activeIndex: result.hits.length === 1 ? 0 : -1,
              }),
            ),
            catchError((error: unknown) => {
              patchState(store, {
                status: 'error',
                result: null,
                error: toUserMessage(error),
                activeIndex: -1,
              });
              return EMPTY;
            }),
          );
        }),
      ),
    );

    return {
      setQuery(query: string): void {
        patchState(store, { query });
        run({ query, immediate: false });
      },
      /** Search now (Enter); skips the typing delay. */
      submit(): void {
        run({ query: store.query(), immediate: true });
      },
      /** `extraOptions`: options after the results that are not results (e.g. "search in the text"). */
      moveActive(delta: 1 | -1, extraOptions = 0): void {
        const count = (store.result()?.hits.length ?? 0) + extraOptions;
        if (count === 0) return;
        const next = store.activeIndex() + delta;
        patchState(store, { activeIndex: (next + count) % count });
      },
      setActive(index: number): void {
        patchState(store, { activeIndex: index });
      },
      clear(): void {
        patchState(store, initialState);
        run({ query: '', immediate: true });
      },
    };
  }),
);
