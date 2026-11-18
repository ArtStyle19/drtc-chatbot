import { HttpErrorResponse } from '@angular/common/http';
import { registerLocaleData } from '@angular/common';
import localeEsPe from '@angular/common/locales/es-PE';
import { LOCALE_ID } from '@angular/core';
import { ComponentFixture, TestBed } from '@angular/core/testing';
import { Title } from '@angular/platform-browser';
import { provideRouter, Router } from '@angular/router';
import { Observable, of, throwError } from 'rxjs';

import { Outline, ReadingUnit } from '../../../core/api/models';
import { FakePdfLoader } from '../../../testing/fake-pdf';
import {
  anEdition,
  anEntry,
  aNode,
  aReadingUnit,
  aRevision,
} from '../../../testing/reader-fixtures';
import { PDF_LOADER } from '../data-access/pdf/pdf-port';
import { ReaderApi } from '../data-access/reader-api';
import { ReaderPage } from './reader-page';

const OUTLINE: Outline = {
  edition: anEdition(),
  entries: [
    anEntry({
      path: 'titulo:I',
      kind: 'title',
      label: 'I',
      title: 'OBJETO',
      parent_path: null,
      unit_path: 'titulo:I',
    }),
    anEntry({
      path: 'articulo:1',
      label: '1',
      title: 'Finalidad',
      parent_path: 'titulo:I',
      unit_path: 'articulo:1',
    }),
    anEntry({
      path: 'articulo:2',
      label: '2',
      title: 'De las definiciones',
      parent_path: 'titulo:I',
      unit_path: 'articulo:2',
    }),
    anEntry({
      path: 'articulo:3',
      label: '3',
      title: 'Autoridades',
      parent_path: 'titulo:I',
      unit_path: 'articulo:3',
    }),
  ],
};

class FakeApi {
  outline$: () => Observable<Outline> = () => of(OUTLINE);
  unit$: (path: string) => Observable<ReadingUnit> = () => of(aReadingUnit());
  outlineCalls = 0;
  unitCalls: string[] = [];
  outline(): Observable<Outline> {
    this.outlineCalls++;
    return this.outline$();
  }
  readingUnit(_id: string, path: string): Observable<ReadingUnit> {
    this.unitCalls.push(path);
    return this.unit$(path);
  }
}

class NoopResizeObserver {
  readonly observe = vi.fn();
  readonly disconnect = vi.fn();
}

async function setup(inputs: { norma?: string; p?: string; v?: string } = {}, api = new FakeApi()) {
  registerLocaleData(localeEsPe);
  vi.stubGlobal('ResizeObserver', NoopResizeObserver);
  TestBed.configureTestingModule({
    providers: [
      provideRouter([]),
      { provide: LOCALE_ID, useValue: 'es-PE' },
      { provide: ReaderApi, useValue: api },
      { provide: PDF_LOADER, useValue: new FakePdfLoader() },
    ],
  });
  const router = TestBed.inject(Router);
  const navigate = vi.spyOn(router, 'navigate').mockResolvedValue(true);
  const fixture = TestBed.createComponent(ReaderPage);
  fixture.componentRef.setInput('norma', inputs.norma ?? 'ley-27181');
  fixture.componentRef.setInput('p', inputs.p);
  fixture.componentRef.setInput('v', inputs.v);
  await settle(fixture);
  return { fixture, el: fixture.nativeElement as HTMLElement, api, navigate };
}

async function settle(fixture: ComponentFixture<ReaderPage>): Promise<void> {
  for (let i = 0; i < 6; i++) {
    fixture.detectChanges();
    await Promise.resolve();
    await fixture.whenStable();
  }
  fixture.detectChanges();
}

const text = (el: Element | null | undefined) => el?.textContent?.replace(/\s+/g, ' ').trim() ?? '';

afterEach(() => vi.unstubAllGlobals());

describe('ReaderPage', () => {
  it('shows the edition, the index and an invitation to choose when no provision is open', async () => {
    const { el, api } = await setup();

    expect(text(el.querySelector('drtc-edition-header h1'))).toBe(
      'Ley General de Transporte y Tránsito Terrestre',
    );
    expect(text(el.querySelector('drtc-validity-seal'))).toContain('No verificado');
    expect(el.querySelector('nav[aria-label="Índice de la norma"]')).not.toBeNull();
    expect(text(el.querySelector('.cover-title'))).toBe('Elija una disposición');
    expect(api.unitCalls).toEqual([]);
  });

  it('opens the provision named by the URL, with its text, history and citation buttons', async () => {
    const { el, api } = await setup({ p: 'articulo:2' });

    expect(api.unitCalls).toEqual(['articulo:2']);
    expect(text(el.querySelector('h2.unit-heading'))).toBe('Artículo 2 De las definiciones');
    expect(text(el.querySelector('.reading .text'))).toContain('Para efectos de la presente Ley');
    expect(text(el.querySelector('details.history summary'))).toBe(
      'Texto anterior, no vigente (1)',
    );
    expect(el.querySelector('.reading drtc-cite-button')).not.toBeNull();
  });

  it('marks the open provision in the index and breadcrumbs its container', async () => {
    const { el } = await setup({ p: 'articulo:2' });

    const current = el.querySelector('drtc-outline-tree [aria-current="location"]');
    expect(text(current)).toBe('Art. 2 De las definiciones');
    expect(text(el.querySelector('nav.breadcrumb'))).toBe('Título I');
  });

  it('shows the validity seal next to the text, not only in the page header', async () => {
    const { el } = await setup({ p: 'articulo:2' });

    expect(text(el.querySelector('.reading .unit-meta drtc-validity-seal'))).toContain(
      'No verificado',
    );
  });

  it('offers the previous and next provisions', async () => {
    const { el } = await setup({ p: 'articulo:2' });

    expect(text(el.querySelector('a.previous'))).toContain('Art. 1 · Finalidad');
    expect(text(el.querySelector('a.next'))).toContain('Art. 3 · Autoridades');
    expect(el.querySelector('a.next')?.getAttribute('href')).toBe(
      '/biblioteca/ley-27181?p=articulo:3',
    );
  });

  it('keeps the chosen edition in every link', async () => {
    const { el } = await setup({ p: 'articulo:2', v: 'ley-27181@2020-05' });

    expect(el.querySelector('a.next')?.getAttribute('href')).toBe(
      '/biblioteca/ley-27181?p=articulo:3&v=ley-27181@2020-05',
    );
  });

  it('shows the PDF of the edition with the passage highlighted', async () => {
    const { el } = await setup({ p: 'articulo:2' });

    expect(el.querySelector('drtc-folio')).not.toBeNull();
    expect(text(el.querySelector('drtc-folio .passage-label'))).toBe('Ley N.° 27181, art. 2');
    expect(text(el.querySelector('drtc-folio .passage-pages'))).toBe('pp. 3-4');
  });

  it('opens a título as a list of what it contains', async () => {
    const api = new FakeApi();
    api.unit$ = () =>
      of(
        aReadingUnit({
          requested_path: 'titulo:I',
          unit_path: 'titulo:I',
          nodes: [
            aNode({
              path: 'titulo:I',
              kind: 'title',
              label: 'I',
              parent_path: null,
              current: aRevision({ title: 'OBJETO', text: '' }),
            }),
          ],
          children: [OUTLINE.entries[1]!, OUTLINE.entries[2]!],
        }),
      );
    const { el } = await setup({ p: 'titulo:I' }, api);

    expect(text(el.querySelector('h2.unit-heading'))).toBe('Título I Objeto');
    expect([...el.querySelectorAll('drtc-container-view a.item')].map((a) => text(a))).toEqual([
      'Art. 1 Finalidad p. 2',
      'Art. 2 De las definiciones p. 2',
    ]);
    expect(el.querySelector('.reading drtc-provision-node')).toBeNull();
  });

  it('highlights a literal inside the open article without loading it again', async () => {
    const { fixture, el, api } = await setup({ p: 'articulo:2' });

    fixture.componentRef.setInput('p', 'articulo:2/literal:e');
    await settle(fixture);

    expect(api.unitCalls).toEqual(['articulo:2']);
    expect(el.querySelector('#p-articulo_2_literal_e')?.classList.contains('is-focused')).toBe(
      true,
    );
    expect(text(el.querySelector('drtc-folio .passage-label'))).toBe(
      'Ley N.° 27181, art. 2, lit. e)',
    );
  });

  it('"Ver en el PDF" puts the passage in the URL, so it can be shared, and shows the PDF pane', async () => {
    const { fixture, el, navigate } = await setup({ p: 'articulo:2' });

    (el.querySelector('#p-articulo_2_literal_e .see') as HTMLButtonElement).click();
    await settle(fixture);

    expect(navigate).toHaveBeenCalledWith(['/biblioteca', 'ley-27181'], {
      queryParams: { p: 'articulo:2/literal:e' },
    });
    expect(el.querySelector('.folio-pane')?.classList.contains('is-active')).toBe(true);
    expect(el.querySelector('.reading')?.classList.contains('is-active')).toBe(false);
  });

  it('shows a replaced text in the PDF as "no vigente"', async () => {
    const { fixture, el } = await setup({ p: 'articulo:2' });

    (el.querySelector('details.history .see') as HTMLButtonElement).click();
    await settle(fixture);

    expect(text(el.querySelector('drtc-folio .badge'))).toBe('Texto anterior · no vigente');
  });

  it('switches between text and PDF on small screens', async () => {
    const { fixture, el } = await setup({ p: 'articulo:2' });
    const [textButton, pdfButton] = [...el.querySelectorAll<HTMLButtonElement>('.panes button')];
    expect(textButton!.getAttribute('aria-pressed')).toBe('true');

    pdfButton!.click();
    await settle(fixture);

    expect(pdfButton!.getAttribute('aria-pressed')).toBe('true');
    expect(textButton!.getAttribute('aria-pressed')).toBe('false');
  });

  it('opens and closes the index panel, telling assistive technology its state', async () => {
    const { fixture, el } = await setup();
    const toggle = el.querySelector('.outline-toggle') as HTMLButtonElement;
    expect(toggle.getAttribute('aria-expanded')).toBe('false');

    toggle.click();
    await settle(fixture);

    expect(toggle.getAttribute('aria-expanded')).toBe('true');
    expect(el.querySelector('.index-panel')?.classList.contains('is-open')).toBe(true);
  });

  it('closes the index panel after choosing a provision', async () => {
    const { fixture, el } = await setup();
    (el.querySelector('.outline-toggle') as HTMLButtonElement).click();
    await settle(fixture);

    fixture.componentRef.setInput('p', 'articulo:1');
    await settle(fixture);

    expect(el.querySelector('.index-panel')?.classList.contains('is-open')).toBe(false);
  });

  it('writes the page title from the provision and the norm', async () => {
    await setup({ p: 'articulo:2' });

    expect(TestBed.inject(Title).getTitle()).toBe('Artículo 2 · Ley 27181 (LGTTT) · DRTC Puno');
  });

  it('explains a norm without an approved edition and lets the person retry', async () => {
    const api = new FakeApi();
    let fail = true;
    api.outline$ = () =>
      fail
        ? throwError(() => new HttpErrorResponse({ status: 404, error: { code: 'not_found' } }))
        : of(OUTLINE);
    const { fixture, el } = await setup({}, api);

    expect(text(el.querySelector('[role="alert"]'))).toContain('No pudimos abrir esta norma.');
    expect(text(el.querySelector('[role="alert"]'))).toContain('no tiene una edición aprobada');
    expect(el.querySelector('drtc-outline-tree')).toBeNull();

    fail = false;
    (el.querySelector('[role="alert"] button') as HTMLButtonElement).click();
    await settle(fixture);

    expect(el.querySelector('[role="alert"]')).toBeNull();
    expect(el.querySelector('drtc-outline-tree')).not.toBeNull();
  });

  it('keeps the index and explains a provision that does not exist', async () => {
    const api = new FakeApi();
    api.unit$ = () => throwError(() => new HttpErrorResponse({ status: 404 }));
    const { el } = await setup({ p: 'articulo:999' }, api);

    expect(text(el.querySelector('.reading [role="alert"]'))).toContain(
      'No encontramos esa disposición',
    );
    expect(el.querySelector('drtc-outline-tree')).not.toBeNull();
  });

  it('loads another norm when the route changes', async () => {
    const { fixture, api } = await setup();

    fixture.componentRef.setInput('norma', 'ds-017-2009-mtc');
    await settle(fixture);

    expect(api.outlineCalls).toBe(2);
  });
});
