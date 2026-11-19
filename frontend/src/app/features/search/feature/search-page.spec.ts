import { HttpErrorResponse } from '@angular/common/http';
import { TestBed } from '@angular/core/testing';
import { Title } from '@angular/platform-browser';
import { provideRouter, Router } from '@angular/router';
import { RouterTestingHarness } from '@angular/router/testing';
import { Observable, of, Subject, throwError } from 'rxjs';

import { SearchResponse } from '../../../core/api/models';
import { searchResponse, searchResult } from '../../../testing/search-fixtures';
import { SearchApi, SearchParams } from '../data-access/search-api';
import { SearchPage } from './search-page';

class FakeApi {
  calls: SearchParams[] = [];
  respond: (params: SearchParams) => Observable<SearchResponse> = () => of(searchResponse());
  search(params: SearchParams): Observable<SearchResponse> {
    this.calls.push(params);
    return this.respond(params);
  }
}

async function open(url: string, api = new FakeApi()) {
  TestBed.configureTestingModule({
    providers: [
      provideRouter([{ path: 'buscar', component: SearchPage }]),
      { provide: SearchApi, useValue: api },
    ],
  });
  const harness = await RouterTestingHarness.create();
  await harness.navigateByUrl(url, SearchPage);
  harness.detectChanges();
  const el = harness.routeNativeElement as HTMLElement;
  const text = (selector: string) =>
    el.querySelector(selector)?.textContent?.replace(/\s+/g, ' ').trim() ?? '';
  const settle = async () => {
    await harness.fixture.whenStable();
    harness.detectChanges();
  };
  return { harness, el, api, text, settle, router: TestBed.inject(Router) };
}

describe('SearchPage', () => {
  it('has one h1, a labelled search form and says what the results are (and are not)', async () => {
    const { el, text } = await open('/buscar');

    expect(el.querySelectorAll('h1')).toHaveLength(1);
    expect(text('h1')).toBe('Buscar en el texto');
    expect(el.querySelector('form')?.getAttribute('role')).toBe('search');
    expect(el.querySelector('label')?.getAttribute('for')).toBe(el.querySelector('input')?.id);
    expect(text('header')).toContain('no son una respuesta ni una opinión legal');
  });

  it('warns not to type personal data, and ties the warning to the field', async () => {
    const { el, text } = await open('/buscar');
    const input = el.querySelector('input')!;

    expect(text('#buscar-privacidad')).toContain('No escriba nombres, DNI, placas');
    expect(input.getAttribute('aria-describedby')).toBe('buscar-privacidad');
    expect(input.maxLength).toBe(300);
  });

  describe('without a text', () => {
    it('does not search and suggests examples that open a search', async () => {
      const { api, el } = await open('/buscar');

      expect(api.calls).toEqual([]);
      const examples = [...el.querySelectorAll<HTMLAnchorElement>('a.example')];
      expect(examples.length).toBeGreaterThan(1);
      expect(new URL(examples[0]!.href).pathname).toBe('/buscar');
      expect(new URL(examples[0]!.href).searchParams.get('q')).toBeTruthy();
    });

    it('does not search for a text of only spaces', async () => {
      const { api } = await open('/buscar?q=%20%20');

      expect(api.calls).toEqual([]);
    });
  });

  describe('the URL decides what is searched', () => {
    it('searches the text of the URL once, and puts it in the box and the title', async () => {
      const { api, el } = await open('/buscar?q=plazo%20para%20apelar');

      expect(api.calls).toEqual([
        { query: 'plazo para apelar', instrument: null, limit: 20, debug: false },
      ]);
      expect(el.querySelector('input')?.value).toBe('plazo para apelar');
      expect(TestBed.inject(Title).getTitle()).toBe('Buscar «plazo para apelar» · DRTC Puno');
    });

    it('searches again when the URL changes (back/forward, shared link)', async () => {
      const { api, router, settle } = await open('/buscar?q=uno');

      await router.navigateByUrl('/buscar?q=dos');
      await settle();

      expect(api.calls.map((c) => c.query)).toEqual(['uno', 'dos']);
    });

    it('takes the norm filter from the URL', async () => {
      const { api, el } = await open('/buscar?q=multa&norma=ds-017-2009-mtc');

      expect(api.calls[0]?.instrument).toBe('ds-017-2009-mtc');
      const pressed = [...el.querySelectorAll('.chip')].filter(
        (c) => c.getAttribute('aria-pressed') === 'true',
      );
      expect(pressed.map((c) => c.textContent?.trim())).toEqual(['RENAT (DS 017-2009-MTC)']);
    });

    it('asks for diagnostics only when the build allows them (this test build is dev mode)', async () => {
      const { api } = await open('/buscar?q=multa&debug=1');

      expect(api.calls[0]?.debug).toBe(true);
    });
  });

  describe('submitting the form', () => {
    it('puts the text in the URL (which searches), dropping the norm filter', async () => {
      const { el, api, router, settle } = await open('/buscar?q=multa&norma=ley-27181');
      const input = el.querySelector('input')!;

      input.value = '  licencia de conducir  ';
      el.querySelector('form')!.dispatchEvent(new Event('submit', { cancelable: true }));
      await settle();

      expect(router.url).toBe('/buscar?q=licencia%20de%20conducir');
      expect(api.calls.at(-1)).toMatchObject({ query: 'licencia de conducir', instrument: null });
    });

    it('does nothing for an empty box and leaves the focus there', async () => {
      const { el, api, router, settle } = await open('/buscar');
      const input = el.querySelector('input')!;
      input.value = '   ';
      const focus = vi.spyOn(input, 'focus');

      el.querySelector('form')!.dispatchEvent(new Event('submit', { cancelable: true }));
      await settle();

      expect(router.url).toBe('/buscar');
      expect(api.calls).toEqual([]);
      expect(focus).toHaveBeenCalled();
    });

    it('does not search while typing', async () => {
      const { el, api, settle } = await open('/buscar');

      el.querySelector('input')!.value = 'mi vecino Pedro DNI 45678912';
      el.querySelector('input')!.dispatchEvent(new Event('input', { bubbles: true }));
      await settle();

      expect(api.calls).toEqual([]);
    });
  });

  describe('results', () => {
    it('announces how many in a status region and lists the cards in an ordered list', async () => {
      const api = new FakeApi();
      api.respond = () =>
        of(
          searchResponse({
            total: 2,
            results: [
              searchResult(),
              searchResult({ unit_path: 'articulo:3', path: 'articulo:3' }),
            ],
          }),
        );
      const { el, text } = await open('/buscar?q=transporte', api);

      expect(el.querySelector('.count')?.getAttribute('role')).toBe('status');
      expect(text('.count')).toBe('2 resultados.');
      expect(el.querySelectorAll('ol.results > li')).toHaveLength(2);
      expect(el.querySelectorAll('drtc-result-card')).toHaveLength(2);
    });

    it('says how many are shown out of how many were found', async () => {
      const api = new FakeApi();
      api.respond = () => of(searchResponse({ total: 35 }));
      const { text } = await open('/buscar?q=transporte', api);

      expect(text('.count')).toBe('Se muestran 1 de 35 resultados.');
    });

    it('says it understood a reference and why it goes first', async () => {
      const api = new FakeApi();
      api.respond = () =>
        of(
          searchResponse({
            reference: 'art. 5',
            results: [
              searchResult({ via: ['reference'] }),
              searchResult({ unit_path: 'articulo:9' }),
            ],
          }),
        );
      const { text } = await open('/buscar?q=art%205%20plazo', api);

      expect(text('.reference-note')).toBe(
        'Se entendió «art. 5» como una referencia exacta: va primero.',
      );
    });

    it('does not claim a reference when the first result is not one', async () => {
      const api = new FakeApi();
      api.respond = () => of(searchResponse({ reference: 'art. 5', results: [searchResult()] }));
      const { el } = await open('/buscar?q=algo', api);

      expect(el.querySelector('.reference-note')).toBeNull();
    });
  });

  describe('filter by norm', () => {
    it('offers every norm of the answer plus "all", and asks the server when one is chosen', async () => {
      const { el, router, settle, api } = await open('/buscar?q=multa');
      const chips = [...el.querySelectorAll<HTMLButtonElement>('.chip')];
      expect(chips.map((c) => c.textContent?.trim())).toEqual([
        'Todas las normas',
        'Ley 27181 (LGTTT)',
        'RENAT (DS 017-2009-MTC)',
      ]);
      expect(el.querySelector('[role="group"]')?.getAttribute('aria-label')).toBe(
        'Filtrar por norma',
      );
      expect(chips[0]?.getAttribute('aria-pressed')).toBe('true');

      chips[2]!.click();
      await settle();

      expect(router.url).toBe('/buscar?q=multa&norma=ds-017-2009-mtc');
      expect(api.calls.at(-1)).toMatchObject({ query: 'multa', instrument: 'ds-017-2009-mtc' });
    });

    it('goes back to every norm with "Todas las normas"', async () => {
      const { el, router, settle } = await open('/buscar?q=multa&norma=ley-27181');

      el.querySelector<HTMLButtonElement>('.chip')!.click();
      await settle();

      expect(router.url).toBe('/buscar?q=multa');
    });

    it('does not offer a filter when there is a single norm and none is chosen', async () => {
      const api = new FakeApi();
      api.respond = () =>
        of(
          searchResponse({ facets: [{ instrument_id: 'ley-27181', short_name: 'Ley', count: 1 }] }),
        );
      const { el } = await open('/buscar?q=multa', api);

      expect(el.querySelector('.chips')).toBeNull();
    });
  });

  describe('states', () => {
    it('shows a skeleton while the first answer is pending, marked busy', async () => {
      const api = new FakeApi();
      api.respond = () => new Subject<SearchResponse>();
      const { el, text } = await open('/buscar?q=multa', api);

      expect(el.querySelectorAll('ul[aria-label="Buscando"] li')).toHaveLength(3);
      expect(el.querySelector('[aria-busy="true"]')).not.toBeNull();
      expect(text('.count')).toBe('Buscando…');
    });

    it('shows the empty state with suggestions and keeps what was asked', async () => {
      const api = new FakeApi();
      api.respond = () => of(searchResponse({ total: 0, results: [], facets: [] }));
      const { el, text } = await open('/buscar?q=zzzz', api);

      expect(text('.count')).toBe('Sin resultados.');
      expect(text('[class*="border-dashed"] p')).toContain(
        'No encontramos coincidencias para «zzzz»',
      );
      expect(el.querySelector('drtc-result-card')).toBeNull();
    });

    it('offers to drop the norm filter when a filtered search finds nothing', async () => {
      const api = new FakeApi();
      api.respond = () => of(searchResponse({ total: 0, results: [] }));
      const { el, router, settle } = await open('/buscar?q=zzzz&norma=ley-27181', api);
      expect(el.textContent).toContain('en Ley 27181 (LGTTT)');

      [...el.querySelectorAll<HTMLButtonElement>('.link-button')]
        .find((b) => b.textContent?.includes('todas las normas'))!
        .click();
      await settle();

      expect(router.url).toBe('/buscar?q=zzzz');
    });

    it('shows a readable error in an alert and retries the same search', async () => {
      const api = new FakeApi();
      api.respond = () => throwError(() => new HttpErrorResponse({ status: 0 }));
      const { el, text, settle } = await open('/buscar?q=multa&norma=ley-27181', api);

      expect(el.querySelector('[role="alert"]')).not.toBeNull();
      expect(text('[role="alert"]')).toContain('No pudimos buscar.');
      expect(text('[role="alert"]')).toContain('No se pudo conectar con el servidor');
      api.respond = () => of(searchResponse());

      [...el.querySelectorAll<HTMLButtonElement>('button')]
        .find((b) => b.textContent?.trim() === 'Reintentar')!
        .click();
      await settle();

      expect(api.calls.at(-1)).toMatchObject({ query: 'multa', instrument: 'ley-27181' });
      expect(el.querySelector('[role="alert"]')).toBeNull();
      expect(el.querySelector('drtc-result-card')).not.toBeNull();
    });
  });

  describe('when the search by meaning is not available', () => {
    it('says so, as a note, and still lists what was found', async () => {
      const api = new FakeApi();
      api.respond = () => of(searchResponse({ degraded: ['vector_unavailable'] }));
      const { el, text } = await open('/buscar?q=multa', api);

      expect(el.querySelector('[role="note"]')).not.toBeNull();
      expect(text('[role="note"]')).toContain(
        'La búsqueda por significado no está disponible ahora',
      );
      expect(el.querySelector('drtc-result-card')).not.toBeNull();
    });

    it('explains an index that has not been prepared differently', async () => {
      const api = new FakeApi();
      api.respond = () => of(searchResponse({ degraded: ['vector_not_indexed'] }));
      const { text } = await open('/buscar?q=multa', api);

      expect(text('[role="note"]')).toContain('aún no se ha preparado');
    });

    it('shows no note when everything worked', async () => {
      const { el } = await open('/buscar?q=multa');

      expect(el.querySelector('[role="note"]')).toBeNull();
    });
  });
});
