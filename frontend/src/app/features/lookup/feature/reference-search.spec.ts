import { HttpErrorResponse } from '@angular/common/http';
import { TestBed } from '@angular/core/testing';
import { Router } from '@angular/router';
import { Observable, of, throwError } from 'rxjs';

import { LookupHit, LookupResult } from '../../../core/api/models';
import { LookupApi } from '../data-access/lookup-api';
import { LOOKUP_DEBOUNCE_MS } from '../data-access/lookup.store';
import { ReferenceSearch } from './reference-search';

function hit(overrides: Partial<LookupHit> = {}): LookupHit {
  return {
    instrument_id: 'ley-27181',
    instrument_short_name: 'Ley 27181 (LGTTT)',
    instrument_title: 'Ley General de Transporte y Tránsito Terrestre',
    citation: 'Ley N.° 27181, art. 5',
    version_id: 'ley-27181@2020-05',
    edition_label: 'Compilación',
    verification_status: 'unverified',
    path: 'articulo:5',
    unit_path: 'articulo:5',
    kind: 'article',
    label: '5',
    title: 'De la competencia',
    snippet: 'El Ministerio de Transportes y Comunicaciones…',
    page_start: 5,
    ...overrides,
  };
}

function result(status: LookupResult['status'], hits: LookupHit[], message = ''): LookupResult {
  return {
    status,
    query: 'q',
    message,
    reference: 'art. 5',
    norms: [],
    total: hits.length,
    hits,
    ignored_text: null,
  };
}

class FakeApi {
  queries: string[] = [];
  response: LookupResult = result('resolved', [hit()]);
  lookup(q: string): Observable<LookupResult> {
    this.queries.push(q);
    return of(this.response);
  }
}

function setup(api = new FakeApi()) {
  TestBed.configureTestingModule({ providers: [{ provide: LookupApi, useValue: api }] });
  const router = TestBed.inject(Router);
  const navigate = vi.spyOn(router, 'navigate').mockResolvedValue(true);
  const fixture = TestBed.createComponent(ReferenceSearch);
  fixture.detectChanges();
  const el = fixture.nativeElement as HTMLElement;
  const input = el.querySelector('input') as HTMLInputElement;

  const type = async (value: string) => {
    input.dispatchEvent(new Event('focusin', { bubbles: true }));
    input.value = value;
    input.dispatchEvent(new Event('input', { bubbles: true }));
    await vi.advanceTimersByTimeAsync(LOOKUP_DEBOUNCE_MS);
    fixture.detectChanges();
  };
  const press = async (key: string) => {
    input.dispatchEvent(new KeyboardEvent('keydown', { key, bubbles: true, cancelable: true }));
    await vi.advanceTimersByTimeAsync(1);
    fixture.detectChanges();
  };
  /** The results of the reference search (not the final «search in the text» option). */
  const options = () => [...el.querySelectorAll<HTMLElement>('[role="option"]:not(.text-option)')];
  const textOption = () => el.querySelector<HTMLElement>('.text-option');
  return { fixture, el, input, api, navigate, type, press, options, textOption };
}

const text = (el: Element | null | undefined) => el?.textContent?.replace(/\s+/g, ' ').trim() ?? '';

describe('ReferenceSearch', () => {
  beforeEach(() => vi.useFakeTimers());
  afterEach(() => vi.useRealTimers());

  it('is a labelled search combobox that starts closed', () => {
    const { el, input } = setup();

    expect(el.querySelector('form')?.getAttribute('role')).toBe('search');
    expect(input.getAttribute('role')).toBe('combobox');
    expect(input.getAttribute('aria-expanded')).toBe('false');
    expect(el.querySelector('label')?.getAttribute('for')).toBe(input.id);
    expect(input.maxLength).toBe(300);
  });

  it('lists the result with the citation written by the server, its page and the edition status', async () => {
    const { type, input, options } = setup();

    await type('art 5 ley 27181');

    expect(input.getAttribute('aria-expanded')).toBe('true');
    expect(options()).toHaveLength(1);
    expect(text(options()[0])).toBe(
      'Ley N.° 27181, art. 5 p. 5 El Ministerio de Transportes y Comunicaciones… Ley 27181 (LGTTT) · edición no verificada',
    );
  });

  it('does not call an edition verified unless the server says so', async () => {
    const api = new FakeApi();
    api.response = result('resolved', [hit({ verification_status: 'verified_current' })]);
    const { type, options } = setup(api);

    await type('art 5');

    expect(text(options()[0])).not.toContain('no verificada');
  });

  it('opens the active result on Enter in the edition where it was found, and clears the field', async () => {
    const { type, press, navigate, input } = setup();
    await type('art 5 ley 27181'); // a single result is already the active one

    await press('Enter');

    expect(navigate).toHaveBeenCalledWith(['/biblioteca', 'ley-27181'], {
      queryParams: { p: 'articulo:5', v: 'ley-27181@2020-05' },
    });
    expect(input.value).toBe('');
  });

  it('goes straight to a single result when Enter is pressed before the answer arrives', async () => {
    const { input, press, navigate, api, fixture } = setup();
    input.dispatchEvent(new Event('focusin', { bubbles: true }));
    input.value = 'art 5 ley 27181';
    input.dispatchEvent(new Event('input', { bubbles: true }));

    await press('Enter'); // before the typing delay: searches now
    fixture.detectChanges();

    expect(api.queries).toEqual(['art 5 ley 27181']);
    expect(navigate).toHaveBeenCalledTimes(1);
  });

  it('never chooses for the person when the reference is ambiguous', async () => {
    const api = new FakeApi();
    api.response = result(
      'ambiguous',
      [
        hit({ citation: 'Ley N.° 27181, art. 11' }),
        hit({ instrument_id: 'ds-017-2009-mtc', citation: 'DS 017-2009-MTC, art. 11' }),
      ],
      'Hay varias normas con «art. 11»: elija una.',
    );
    const { input, press, navigate, options, el } = setup(api);
    input.dispatchEvent(new Event('focusin', { bubbles: true }));
    input.value = 'art 11';
    input.dispatchEvent(new Event('input', { bubbles: true }));

    await press('Enter');

    expect(navigate).not.toHaveBeenCalled();
    expect(options()).toHaveLength(2);
    expect(text(el.querySelector('.message'))).toBe('Hay varias normas con «art. 11»: elija una.');
  });

  it('moves through the results with the arrows, announced through aria-activedescendant', async () => {
    const api = new FakeApi();
    api.response = result('ambiguous', [
      hit(),
      hit({ path: 'articulo:6', citation: 'Ley N.° 27181, art. 6' }),
    ]);
    const { type, press, input, options, textOption } = setup(api);
    await type('art');

    await press('ArrowDown');
    expect(input.getAttribute('aria-activedescendant')).toBe(options()[0]!.id);
    expect(options()[0]!.getAttribute('aria-selected')).toBe('true');

    await press('ArrowDown');
    expect(input.getAttribute('aria-activedescendant')).toBe(options()[1]!.id);

    await press('ArrowDown'); // the last stop is the way out to the text search
    expect(input.getAttribute('aria-activedescendant')).toBe(textOption()!.id);
    expect(textOption()!.getAttribute('aria-selected')).toBe('true');

    await press('ArrowDown'); // wraps
    expect(options()[0]!.getAttribute('aria-selected')).toBe('true');
  });

  it('opens a result when it is clicked', async () => {
    const { type, options, navigate } = setup();
    await type('art 5');

    options()[0]!.click();

    expect(navigate).toHaveBeenCalledTimes(1);
  });

  it('opens a whole norm without a path', async () => {
    const api = new FakeApi();
    api.response = result('resolved', [
      hit({
        path: null,
        unit_path: null,
        citation: 'TUO de la Ley 27444',
        snippet: null,
        page_start: null,
      }),
    ]);
    const { type, options, press, navigate } = setup(api);
    await type('LPAG');

    expect(text(options()[0])).toContain('TUO de la Ley 27444');
    await press('Enter');

    expect(navigate).toHaveBeenCalledWith(['/biblioteca', 'ley-27181'], {
      queryParams: { v: 'ley-27181@2020-05' },
    });
  });

  it('explains what it did not understand, without a list', async () => {
    const api = new FakeApi();
    api.response = {
      ...result(
        'unrecognized',
        [],
        'No reconozco una referencia, pero puede buscarlo por su contenido.',
      ),
      ignored_text: 'transporte',
    };
    const { type, el, options, textOption } = setup(api);

    await type('transporte de mercancías');

    expect(options()).toHaveLength(0); // no reference results...
    expect(text(textOption())).toBe('Buscar «transporte de mercancías» en el texto'); // ...only the way out
    expect(text(el.querySelector('.message'))).toContain('puede buscarlo por su contenido');
    expect(text(el.querySelector('.ignored'))).toBe('No tuve en cuenta: «transporte»');
  });

  describe('«Buscar … en el texto»', () => {
    it('is the last option whatever the reference search answered', async () => {
      for (const status of ['resolved', 'ambiguous', 'not_found'] as const) {
        const api = new FakeApi();
        api.response = result(
          status,
          status === 'not_found' ? [] : [hit(), hit({ path: 'articulo:6' })],
        );
        const { type, el, textOption, fixture } = setup(api);

        await type('plazo de apelación');

        const options = [...el.querySelectorAll('[role="option"]')];
        expect(options.at(-1)).toBe(textOption());
        expect(text(textOption())).toBe('Buscar «plazo de apelación» en el texto');
        fixture.destroy();
        TestBed.resetTestingModule();
      }
    });

    it('is offered while the reference search is still loading', async () => {
      const { input, textOption, fixture } = setup();
      input.dispatchEvent(new Event('focusin', { bubbles: true }));
      input.value = 'plazo';
      input.dispatchEvent(new Event('input', { bubbles: true }));
      fixture.detectChanges();

      expect(text(textOption())).toBe('Buscar «plazo» en el texto');
    });

    it('goes to /buscar with the trimmed text when it is clicked, and clears the field', async () => {
      const { type, textOption, navigate, input, fixture } = setup();
      await type('  plazo para apelar  ');

      textOption()!.click();
      fixture.detectChanges();

      expect(navigate).toHaveBeenCalledExactlyOnceWith(['/buscar'], {
        queryParams: { q: 'plazo para apelar' },
      });
      expect(input.value).toBe('');
    });

    it('is reached with the arrows and chosen with Enter', async () => {
      const { type, press, navigate } = setup(); // one result, already active

      await type('art 5 ley 27181');
      await press('ArrowDown');
      await press('Enter');

      expect(navigate).toHaveBeenCalledExactlyOnceWith(['/buscar'], {
        queryParams: { q: 'art 5 ley 27181' },
      });
    });

    it('takes the person there on Enter when the text is not a reference at all', async () => {
      const api = new FakeApi();
      api.response = result('unrecognized', [], 'No reconozco una referencia.');
      const { input, press, navigate, fixture } = setup(api);
      input.dispatchEvent(new Event('focusin', { bubbles: true }));
      input.value = 'se puede cobrar por mototaxi';
      input.dispatchEvent(new Event('input', { bubbles: true }));

      await press('Enter'); // before the answer: it waits for it, then decides
      fixture.detectChanges();

      expect(navigate).toHaveBeenCalledExactlyOnceWith(['/buscar'], {
        queryParams: { q: 'se puede cobrar por mototaxi' },
      });
    });

    it('does NOT leave for the text search by itself: an unknown reference stays here', async () => {
      const api = new FakeApi();
      api.response = result('not_found', [], 'La Ley 27181 no tiene art. 999.');
      const { input, press, navigate, fixture } = setup(api);
      input.dispatchEvent(new Event('focusin', { bubbles: true }));
      input.value = 'art 999 ley 27181';
      input.dispatchEvent(new Event('input', { bubbles: true }));

      await press('Enter');
      fixture.detectChanges();

      expect(navigate).not.toHaveBeenCalled();
    });
  });

  it('closes on Escape and clears the field on a second Escape', async () => {
    const { type, press, input, el } = setup();
    await type('art 5');

    await press('Escape');
    expect(input.getAttribute('aria-expanded')).toBe('false');
    expect(el.querySelector('.panel')).toBeNull();
    expect(input.value).toBe('art 5');

    await press('Escape');
    expect(input.value).toBe('');
  });

  it('jumps to the field with "/" unless the person is typing somewhere else', () => {
    const { input, fixture } = setup();
    const focus = vi.spyOn(input, 'focus');

    document.body.dispatchEvent(new KeyboardEvent('keydown', { key: '/', bubbles: true }));
    expect(focus).toHaveBeenCalledTimes(1);

    const other = document.createElement('input');
    document.body.append(other);
    other.dispatchEvent(new KeyboardEvent('keydown', { key: '/', bubbles: true }));
    expect(focus).toHaveBeenCalledTimes(1);
    other.remove();
    fixture.destroy();
  });

  it('shows a failure in Spanish', async () => {
    const api = new FakeApi();
    api.lookup = () => throwError(() => new HttpErrorResponse({ status: 0 }));
    const { type, el } = setup(api);

    await type('art 5');

    expect(text(el.querySelector('.message'))).toContain('No se pudo conectar');
  });
});
