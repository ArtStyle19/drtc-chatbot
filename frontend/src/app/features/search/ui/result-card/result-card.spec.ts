import { Component } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';

import { SearchResult } from '../../../../core/api/models';
import { searchResult } from '../../../../testing/search-fixtures';
import { ResultCard } from './result-card';

@Component({
  imports: [ResultCard],
  template: '<drtc-result-card [result]="result" [diagnostics]="diagnostics" />',
})
class Host {
  result: SearchResult = searchResult();
  diagnostics = false;
}

/** The path and parameters of a link, decoded (the router percent-encodes `/` and `@`). */
function target(link: Element | null | undefined) {
  const url = new URL(link?.getAttribute('href') ?? '', 'http://localhost');
  return { path: url.pathname, p: url.searchParams.get('p'), v: url.searchParams.get('v') };
}

function render(result: SearchResult, diagnostics = false) {
  TestBed.configureTestingModule({ providers: [provideRouter([])] });
  const fixture = TestBed.createComponent(Host);
  fixture.componentInstance.result = result;
  fixture.componentInstance.diagnostics = diagnostics;
  fixture.detectChanges();
  const el = fixture.nativeElement as HTMLElement;
  const text = (selector: string) =>
    el.querySelector(selector)?.textContent?.replace(/\s+/g, ' ').trim();
  return { fixture, el, text };
}

describe('ResultCard', () => {
  it('shows the citation written by the server, the norm, the title and the page', () => {
    const { text } = render(searchResult());

    expect(text('.reference')).toBe('Ley 27181 (LGTTT)');
    expect(text('.title')).toBe('Ley N.° 27181, art. 2, lit. e)');
    expect(text('.subtitle')).toBe('Definiciones');
    expect(text('.foot .page')).toBe('p. 3');
  });

  it('writes a range of pages as a range', () => {
    const { text } = render(searchResult({ page_start: 12, page_end: 13 }));

    expect(text('.foot .page')).toBe('pp. 12–13');
  });

  it('is labelled by its citation', () => {
    const { el } = render(searchResult());
    const article = el.querySelector('article')!;

    expect(article.getAttribute('aria-labelledby')).toBe(el.querySelector('.title')!.id);
  });

  it('shows no empty line for an article that has no text of its own', () => {
    const { el } = render(searchResult({ snippet: [], matched: [], via: ['reference'] }));

    expect(el.querySelector('.snippet')).toBeNull();
    expect(el.querySelector('.title')).not.toBeNull();
  });

  it('marks the words that matched and keeps the spaces around them', () => {
    const { el, text } = render(searchResult());

    expect(text('.snippet')).toBe('Servicio de transporte de personas.');
    expect(el.querySelector('.snippet mark')?.textContent).toBe('transporte');
  });

  describe('the validity seal', () => {
    it('says "No verificado" for an unverified edition and shows its label', () => {
      const { text } = render(searchResult());

      expect(text('drtc-validity-seal')).toContain('No verificado');
      expect(text('.edition')).toBe('Compilación no oficial hasta mayo de 2020');
    });

    it('shows "verified" only when the server also allows presenting it as current', () => {
      const ok = render(
        searchResult({
          verification_status: 'verified_current',
          may_be_presented_as_current: true,
        }),
      );
      expect(ok.text('drtc-validity-seal')).toContain('Vigente verificado');
      TestBed.resetTestingModule();

      const inconsistent = render(
        searchResult({
          verification_status: 'verified_current',
          may_be_presented_as_current: false,
        }),
      );
      expect(inconsistent.text('drtc-validity-seal')).not.toContain('Vigente verificado');
      expect(inconsistent.text('drtc-validity-seal')).toContain('No verificado');
    });

    it('shows a repealed or unknown status as such, never as current', () => {
      const repealed = render(searchResult({ verification_status: 'repealed' }));
      expect(repealed.text('drtc-validity-seal')).toContain('Derogado');
      TestBed.resetTestingModule();

      const unknown = render(searchResult({ verification_status: 'something-new' }));
      expect(unknown.text('drtc-validity-seal')).toContain('Vigencia desconocida');
    });
  });

  it('links to the reader at the exact passage and in the edition it came from', () => {
    const { el } = render(searchResult());
    const link = el.querySelector<HTMLAnchorElement>('a.read')!;

    expect(target(link)).toEqual({
      path: '/biblioteca/ley-27181',
      p: 'articulo:2/literal:e',
      v: 'ley-27181@2020-05',
    });
    expect(link.textContent).toContain('Leer en la norma');
    expect(link.querySelector('.sr-only')?.textContent).toContain('art. 2, lit. e)');
  });

  describe('how it was found', () => {
    it('labels each method in words, not only by colour', () => {
      const { el } = render(searchResult({ via: ['lexical', 'vector'] }));

      expect([...el.querySelectorAll('.via')].map((v) => v.textContent)).toEqual([
        'Por palabras',
        'Por significado',
      ]);
      expect(el.querySelector('.vias')?.getAttribute('aria-label')).toBe('Cómo se encontró');
    });

    it('marks an exact reference, which is placed first on purpose', () => {
      const { el, text } = render(searchResult({ via: ['reference'] }));

      expect(el.querySelector('article')?.getAttribute('data-exact')).toBe('true');
      expect(text('.via')).toBe('Referencia exacta');
    });

    it('does not mark the others as exact', () => {
      const { el } = render(searchResult({ via: ['vector'] }));

      expect(el.querySelector('article')?.getAttribute('data-exact')).toBe('false');
    });
  });

  describe('other matching passages of the same unit', () => {
    const other = (path: string, citation: string) => ({
      path,
      citation,
      page_start: 3,
      page_end: 4,
      snippet: [{ text: 'otro texto', match: false }],
    });

    it('lists them in a disclosure, the main one is not repeated', () => {
      const first = searchResult().matched[0]!;
      const { el, text } = render(
        searchResult({
          matched: [
            first,
            other('articulo:2/literal:a', 'art. 2, lit. a)'),
            other('articulo:2/literal:b', 'art. 2, lit. b)'),
          ],
        }),
      );

      expect(text('.others summary')).toContain('2 pasajes más coinciden');
      const links = [...el.querySelectorAll<HTMLAnchorElement>('.other-link')];
      expect(links.map((a) => a.textContent?.trim())).toEqual([
        'art. 2, lit. a)',
        'art. 2, lit. b)',
      ]);
      expect(target(links[0])).toEqual({
        path: '/biblioteca/ley-27181',
        p: 'articulo:2/literal:a',
        v: 'ley-27181@2020-05',
      });
      expect(el.querySelectorAll('.others li .page')[0]?.textContent).toBe('pp. 3–4');
    });

    it('uses the singular for one', () => {
      const first = searchResult().matched[0]!;
      const { text } = render(
        searchResult({ matched: [first, other('articulo:2/literal:a', 'a')] }),
      );

      expect(text('.others summary')).toContain('Otro pasaje coincide');
    });

    it('has no disclosure when only the main passage matched', () => {
      const { el } = render(searchResult());

      expect(el.querySelector('.others')).toBeNull();
    });
  });

  describe('diagnostics', () => {
    const debug = { lexical_rank: 2, vector_rank: null, reference_rank: 'x' };

    it('is hidden unless asked for', () => {
      const { el } = render(searchResult({ debug }), false);

      expect(el.querySelector('.debug')).toBeNull();
    });

    it('shows what the server reported when asked for', () => {
      const { el } = render(searchResult({ debug }), true);

      expect([...el.querySelectorAll('.debug dt')].map((d) => d.textContent)).toEqual([
        'lexical_rank',
        'vector_rank',
        'reference_rank',
      ]);
      expect([...el.querySelectorAll('.debug dd')].map((d) => d.textContent)).toEqual([
        '2',
        'null',
        'x',
      ]);
    });

    it('shows nothing when asked for but the server sent no diagnostics (production)', () => {
      const { el } = render(searchResult({ debug: null }), true);

      expect(el.querySelector('.debug')).toBeNull();
    });
  });
});
