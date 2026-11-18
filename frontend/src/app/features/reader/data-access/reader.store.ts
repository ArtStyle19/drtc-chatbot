import { computed, inject } from '@angular/core';
import { patchState, signalStore, withComputed, withMethods, withState } from '@ngrx/signals';
import { firstValueFrom } from 'rxjs';

import { Outline, ReadingUnit } from '../../../core/api/models';
import { toUserMessage } from '../../../core/http/problem-details';
import { buildOutlineTree, entryForPath } from './outline-tree';
import { ReaderApi } from './reader-api';
import { buildReadingTree, currentTarget, FolioTarget, historyTarget } from './reading-tree';

export type LoadStatus = 'idle' | 'loading' | 'ready' | 'error';

interface ReaderState {
  readonly instrumentId: string | null;
  readonly versionId: string | null;
  readonly outline: Outline | null;
  readonly outlineStatus: LoadStatus;
  readonly outlineError: string | null;
  readonly unit: ReadingUnit | null;
  readonly unitStatus: LoadStatus;
  readonly unitError: string | null;
  /** The path the person is looking at (the URL's `p`); may be inside the loaded unit. */
  readonly focusPath: string | null;
  /** A replaced text being shown in the Folio instead of the current one. */
  readonly history: { readonly path: string; readonly revision: number } | null;
}

const initialState: ReaderState = {
  instrumentId: null,
  versionId: null,
  outline: null,
  outlineStatus: 'idle',
  outlineError: null,
  unit: null,
  unitStatus: 'idle',
  unitError: null,
  focusPath: null,
  history: null,
};

function unitContains(unit: ReadingUnit, path: string): boolean {
  return path === unit.unit_path || path.startsWith(unit.unit_path + '/');
}

/** State of the reader page: the norm's outline, the reading unit and what the Folio shows. */
export const ReaderStore = signalStore(
  withState(initialState),
  withComputed((store) => {
    const entries = computed(() => store.outline()?.entries ?? []);
    return {
      edition: computed(() => store.outline()?.edition ?? store.unit()?.edition ?? null),
      entries,
      tree: computed(() => buildOutlineTree(entries())),
      currentEntry: computed(() => entryForPath(entries(), store.focusPath())),
      unitTree: computed(() => buildReadingTree(store.unit()?.nodes ?? [])),
      folioTarget: computed((): FolioTarget | null => {
        const unit = store.unit();
        const focus = store.focusPath();
        if (!unit) return null;
        const history = store.history();
        if (history) {
          return historyTarget(
            unit.nodes,
            history.path,
            history.revision,
            `Texto anterior (no vigente) · rev. ${history.revision}`,
          );
        }
        if (!focus) return null;
        const label = unit.nodes.find((n) => n.path === focus)?.current.citation.short ?? '';
        return currentTarget(unit.nodes, focus, label);
      }),
    };
  }),
  withMethods((store, api = inject(ReaderApi)) => {
    // Responses of superseded requests must never overwrite a newer one.
    let outlineRequest = 0;
    let unitRequest = 0;

    const loadUnit = async (path: string): Promise<void> => {
      const instrumentId = store.instrumentId();
      if (!instrumentId) return;
      const request = ++unitRequest;
      patchState(store, { unitStatus: 'loading', unitError: null });
      try {
        const unit = await firstValueFrom(api.readingUnit(instrumentId, path, store.versionId()));
        if (request === unitRequest) patchState(store, { unit, unitStatus: 'ready' });
      } catch (error: unknown) {
        if (request === unitRequest) {
          patchState(store, {
            unit: null,
            unitStatus: 'error',
            unitError: toUserMessage(error, {
              notFound: 'No encontramos esa disposición en la edición cargada.',
            }),
          });
        }
      }
    };

    const loadOutline = async (): Promise<void> => {
      const instrumentId = store.instrumentId();
      if (!instrumentId) return;
      const request = ++outlineRequest;
      patchState(store, { outlineStatus: 'loading', outlineError: null });
      try {
        const outline = await firstValueFrom(api.outline(instrumentId, store.versionId()));
        if (request === outlineRequest) patchState(store, { outline, outlineStatus: 'ready' });
      } catch (error: unknown) {
        if (request === outlineRequest) {
          patchState(store, {
            outline: null,
            outlineStatus: 'error',
            outlineError: toUserMessage(error, {
              notFound: 'Esta norma no tiene una edición aprobada para leer.',
            }),
          });
        }
      }
    };

    return {
      /** Opens a norm (and edition). Reopening the same one keeps what is already loaded. */
      async open(instrumentId: string, versionId: string | null): Promise<void> {
        if (
          store.instrumentId() === instrumentId &&
          store.versionId() === versionId &&
          store.outlineStatus() !== 'error'
        ) {
          return;
        }
        unitRequest++; // drop any in-flight unit of the previous norm
        patchState(store, { ...initialState, instrumentId, versionId });
        await loadOutline();
      },

      /** Focuses a path (the URL's `p`). Loads its reading unit unless it is already loaded. */
      async focus(path: string | null): Promise<void> {
        patchState(store, { focusPath: path, history: null });
        if (!path) {
          unitRequest++;
          patchState(store, { unit: null, unitStatus: 'idle', unitError: null });
          return;
        }
        const unit = store.unit();
        if (unit && store.unitStatus() === 'ready' && unitContains(unit, path)) return;
        await loadUnit(path);
      },

      showHistory(path: string, revision: number): void {
        patchState(store, { history: { path, revision } });
      },

      hideHistory(): void {
        patchState(store, { history: null });
      },

      retryOutline: loadOutline,

      async retryUnit(): Promise<void> {
        const path = store.focusPath();
        if (path) await loadUnit(path);
      },
    };
  }),
);
