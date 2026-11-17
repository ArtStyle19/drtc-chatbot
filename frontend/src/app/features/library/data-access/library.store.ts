import { computed, inject } from '@angular/core';
import {
  patchState,
  signalStore,
  withComputed,
  withHooks,
  withMethods,
  withState,
} from '@ngrx/signals';
import { firstValueFrom } from 'rxjs';

import { LegalInstrument } from '../../../core/api/models';
import { toUserMessage } from '../../../core/http/problem-details';
import { LibraryApi } from './library-api';

type LoadStatus = 'idle' | 'loading' | 'loaded' | 'error';

interface LibraryState {
  readonly instruments: readonly LegalInstrument[];
  readonly status: LoadStatus;
  readonly errorMessage: string | null;
}

const initialState: LibraryState = { instruments: [], status: 'idle', errorMessage: null };

/** State of the Biblioteca page. Provided by the page component (one instance per visit). */
export const LibraryStore = signalStore(
  withState(initialState),
  withComputed(({ instruments, status }) => ({
    isLoading: computed(() => status() === 'loading' || status() === 'idle'),
    isEmpty: computed(() => status() === 'loaded' && instruments().length === 0),
    unverifiedCount: computed(
      () =>
        instruments().filter((item) => !item.current_edition.may_be_presented_as_current).length,
    ),
  })),
  withMethods((store, api = inject(LibraryApi)) => ({
    async load(): Promise<void> {
      patchState(store, { status: 'loading', errorMessage: null });
      try {
        const instruments = await firstValueFrom(api.listInstruments());
        patchState(store, { instruments, status: 'loaded' });
      } catch (error: unknown) {
        patchState(store, { status: 'error', errorMessage: toUserMessage(error) });
      }
    },
  })),
  withHooks({
    onInit(store) {
      void store.load();
    },
  }),
);
