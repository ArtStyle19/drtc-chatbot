import { HttpErrorResponse } from '@angular/common/http';
import { TestBed } from '@angular/core/testing';
import { Observable, of, Subject, throwError } from 'rxjs';

import { Outline, ReadingUnit } from '../../../core/api/models';
import { anEdition, anEntry, aReadingUnit } from '../../../testing/reader-fixtures';
import { ReaderApi } from './reader-api';
import { ReaderStore } from './reader.store';

const OUTLINE: Outline = {
  edition: anEdition(),
  entries: [
    anEntry({
      path: 'titulo:I',
      kind: 'title',
      label: 'I',
      parent_path: null,
      unit_path: 'titulo:I',
    }),
    anEntry(),
    anEntry({ path: 'articulo:3', label: '3', parent_path: null, unit_path: 'articulo:3' }),
  ],
};

class FakeApi {
  outlineCalls: [string, string | null][] = [];
  unitCalls: string[] = [];
  outline$: () => Observable<Outline> = () => of(OUTLINE);
  unit$: (path: string) => Observable<ReadingUnit> = () => of(aReadingUnit());

  outline(id: string, version: string | null): Observable<Outline> {
    this.outlineCalls.push([id, version]);
    return this.outline$();
  }
  readingUnit(_id: string, path: string): Observable<ReadingUnit> {
    this.unitCalls.push(path);
    return this.unit$(path);
  }
}

function setup(api = new FakeApi()) {
  TestBed.configureTestingModule({
    providers: [ReaderStore, { provide: ReaderApi, useValue: api }],
  });
  return { store: TestBed.inject(ReaderStore), api };
}

describe('ReaderStore', () => {
  it('loads the outline of a norm and exposes the nested tree and the edition', async () => {
    const { store } = setup();

    await store.open('ley-27181', null);

    expect(store.outlineStatus()).toBe('ready');
    expect(store.edition()?.verification_status).toBe('unverified');
    expect(store.tree().map((n) => n.entry.path)).toEqual(['titulo:I', 'articulo:3']); // articulo:2 is under titulo:I
    expect(store.tree()[0]?.children.map((n) => n.entry.path)).toEqual(['articulo:2']);
  });

  it('keeps what is loaded when the same norm is opened again, and reloads for another one', async () => {
    const { store, api } = setup();

    await store.open('ley-27181', null);
    await store.open('ley-27181', null);
    await store.open('ds-017-2009-mtc', 'v1');

    expect(api.outlineCalls).toEqual([
      ['ley-27181', null],
      ['ds-017-2009-mtc', 'v1'],
    ]);
  });

  it('explains a missing edition without showing the technical error', async () => {
    const api = new FakeApi();
    api.outline$ = () =>
      throwError(
        () =>
          new HttpErrorResponse({
            status: 404,
            error: { code: 'not_found', detail: 'ley-1 has no approved edition' },
          }),
      );
    const { store } = setup(api);

    await store.open('ley-1', null);

    expect(store.outlineStatus()).toBe('error');
    expect(store.outlineError()).toBe('Esta norma no tiene una edición aprobada para leer.');
  });

  it('loads the reading unit of the focused path and highlights it in the Folio', async () => {
    const { store, api } = setup();
    await store.open('ley-27181', null);

    await store.focus('articulo:2/literal:e');

    expect(api.unitCalls).toEqual(['articulo:2/literal:e']);
    expect(store.currentEntry()?.path).toBe('articulo:2');
    expect(store.folioTarget()).toMatchObject({
      label: 'Ley N.° 27181, art. 2, lit. e)',
      pageStart: 3,
      pageEnd: 4,
      replaced: false,
    });
  });

  it('does not reload while moving inside the loaded unit', async () => {
    const { store, api } = setup();
    await store.open('ley-27181', null);

    await store.focus('articulo:2');
    await store.focus('articulo:2/literal:a');
    await store.focus('articulo:2/literal:e');

    expect(api.unitCalls).toEqual(['articulo:2']);
    expect(store.folioTarget()?.boxes).toHaveLength(2);
  });

  it('shows a replaced text in the Folio and goes back to the current one', async () => {
    const { store } = setup();
    await store.open('ley-27181', null);
    await store.focus('articulo:2');

    store.showHistory('articulo:2', 1);
    expect(store.folioTarget()).toMatchObject({ replaced: true, pageStart: 2 });

    store.hideHistory();
    expect(store.folioTarget()?.replaced).toBe(false);
  });

  it('never lets a slow answer for an old selection replace a newer one', async () => {
    const api = new FakeApi();
    const slow = new Subject<ReadingUnit>();
    api.unit$ = (path) =>
      path === 'articulo:1'
        ? slow
        : of(aReadingUnit({ unit_path: 'articulo:3', requested_path: 'articulo:3' }));
    const { store } = setup(api);
    await store.open('ley-27181', null);

    const first = store.focus('articulo:1'); // slow, still pending
    await store.focus('articulo:3'); // newer, answers at once
    slow.next(aReadingUnit({ unit_path: 'articulo:1', requested_path: 'articulo:1' }));
    slow.complete();
    await first;

    expect(store.unit()?.unit_path).toBe('articulo:3');
  });

  it('reports a missing disposition and lets the person retry', async () => {
    const api = new FakeApi();
    let fail = true;
    api.unit$ = () =>
      fail ? throwError(() => new HttpErrorResponse({ status: 404 })) : of(aReadingUnit());
    const { store } = setup(api);
    await store.open('ley-27181', null);

    await store.focus('articulo:999');
    expect(store.unitError()).toBe('No encontramos esa disposición en la edición cargada.');

    fail = false;
    await store.retryUnit();
    expect(store.unitStatus()).toBe('ready');
  });

  it('clears the reading unit when nothing is focused', async () => {
    const { store } = setup();
    await store.open('ley-27181', null);
    await store.focus('articulo:2');

    await store.focus(null);

    expect(store.unit()).toBeNull();
    expect(store.folioTarget()).toBeNull();
  });
});
