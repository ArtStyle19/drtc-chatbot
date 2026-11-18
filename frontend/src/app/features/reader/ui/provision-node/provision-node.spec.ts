import { registerLocaleData } from '@angular/common';
import localeEsPe from '@angular/common/locales/es-PE';
import { LOCALE_ID } from '@angular/core';
import { TestBed } from '@angular/core/testing';

import { aNode, aReadingUnit } from '../../../../testing/reader-fixtures';
import { buildReadingTree } from '../../data-access/reading-tree';
import { HistorySelection, ProvisionNode } from './provision-node';

function render(
  options: {
    focus?: string | null;
    nodes?: ReturnType<typeof aReadingUnit>['nodes'];
    depth?: number;
  } = {},
) {
  registerLocaleData(localeEsPe);
  TestBed.configureTestingModule({ providers: [{ provide: LOCALE_ID, useValue: 'es-PE' }] });
  const fixture = TestBed.createComponent(ProvisionNode);
  const [root] = buildReadingTree(options.nodes ?? aReadingUnit().nodes);
  fixture.componentRef.setInput('tree', root);
  fixture.componentRef.setInput('depth', options.depth ?? 0);
  fixture.componentRef.setInput('focusPath', options.focus ?? null);
  const focused: string[] = [];
  const history: HistorySelection[] = [];
  fixture.componentInstance.viewPassage.subscribe((path) => focused.push(path));
  fixture.componentInstance.showHistory.subscribe((h) => history.push(h));
  fixture.detectChanges();
  return { fixture, el: fixture.nativeElement as HTMLElement, focused, history };
}

const text = (el: Element | null | undefined) => el?.textContent?.replace(/\s+/g, ' ').trim() ?? '';

describe('ProvisionNode', () => {
  it('shows the locator, the page and the current text', () => {
    const { el } = render();

    expect(text(el.querySelector(':scope > .head .locator'))).toBe('Artículo 2');
    expect(text(el.querySelector(':scope > .head .pages'))).toBe('p. 3');
    expect(text(el.querySelector(':scope > .text'))).toBe(
      'Para efectos de la presente Ley, entiéndase por:',
    );
  });

  it('nests the literals below the article', () => {
    const { el } = render();

    const children = [...el.querySelectorAll(':scope > .children > li > drtc-provision-node')];
    expect(children.map((c) => text(c.querySelector('.locator')))).toEqual(['a)', 'e)']);
    expect(children.map((c) => c.getAttribute('data-kind'))).toEqual(['literal', 'literal']);
  });

  it('says which norm modified the current text, with the date', () => {
    const { el } = render();

    expect(text(el.querySelector(':scope > .event'))).toBe(
      'Texto modificado por el Decreto de Urgencia Nº 019-2020 (24 de enero de 2020)',
    );
  });

  it('keeps the replaced text apart, labelled as no longer in force and cited as such', () => {
    const { el } = render();

    const history = el.querySelector(':scope > details.history') as HTMLDetailsElement;
    expect(text(history.querySelector('summary'))).toBe('Texto anterior, no vigente (1)');
    expect(history.open).toBe(false);
    expect(text(history.querySelector('.not-in-force'))).toBe('No vigente');
    expect(text(history.querySelector('.old-text'))).toBe('Texto anterior del artículo.');
    expect(text(history.querySelector('.event'))).toContain(
      'Sustituido por el Decreto de Urgencia Nº 019-2020',
    );
    expect(el.querySelector(':scope > .text')?.textContent).not.toContain('Texto anterior');
  });

  it('shows a visible warning when a paragraph replacement could not be applied', () => {
    const { el } = render();

    const warning = el.querySelector(':scope > .children > li:last-child .warning');
    expect(warning?.getAttribute('role')).toBe('note');
    expect(text(warning)).toContain('Una norma posterior sustituyó un párrafo');
  });

  it('lists editorial notes separately and collapsed', () => {
    const { el } = render();

    const notes = el.querySelector(':scope > details.notes') as HTMLDetailsElement;
    expect(text(notes.querySelector('summary'))).toBe('Notas editoriales (1)');
    expect(notes.open).toBe(false);
    expect(text(notes.querySelector('.note-kind'))).toBe('Nota de modificación');
    expect(el.querySelector(':scope > .text')?.textContent).not.toContain('(**)');
  });

  it('asks for the passage to be shown in the PDF, saying which one for screen readers', () => {
    const { el, focused } = render();
    const literal = el.querySelector(
      ':scope > .children > li:last-child > drtc-provision-node',
    ) as HTMLElement;

    (literal.querySelector('.see') as HTMLButtonElement).click();

    expect(focused).toEqual(['articulo:2/literal:e']);
    expect(text(literal.querySelector('.see'))).toBe(
      'Ver en el PDF de Ley N.° 27181, art. 2, lit. e)',
    );
  });

  it('asks for the replaced text to be shown in the PDF', () => {
    const { el, history } = render();

    (el.querySelector(':scope > details.history .see') as HTMLButtonElement).click();

    expect(history).toEqual([{ path: 'articulo:2', revision: 1 }]);
  });

  it('marks the focused node and what is inside the focused passage', () => {
    const { el } = render({ focus: 'articulo:2/literal:e' });

    expect(el.classList.contains('is-focused')).toBe(false);
    expect(
      el
        .querySelector(':scope > .children > li:last-child > drtc-provision-node')
        ?.classList.contains('is-focused'),
    ).toBe(true);
    expect(
      el
        .querySelector(':scope > .children > li:first-child > drtc-provision-node')
        ?.classList.contains('is-focused'),
    ).toBe(false);
  });

  it('highlights a whole numeral including its literals', () => {
    const nodes = [
      aNode({
        path: 'articulo:5/numeral:5.2',
        kind: 'numeral',
        label: '5.2',
        parent_path: 'articulo:5',
      }),
      aNode({
        path: 'articulo:5/numeral:5.2/literal:a',
        kind: 'literal',
        label: 'a',
        parent_path: 'articulo:5/numeral:5.2',
      }),
    ];
    const { el } = render({ nodes, focus: 'articulo:5/numeral:5.2' });

    expect(el.classList.contains('is-focused')).toBe(true);
    expect(
      el
        .querySelector(':scope > .children > li > drtc-provision-node')
        ?.classList.contains('in-focus'),
    ).toBe(true);
  });

  it('shows the text of an annex in its own scrollable region and flags its warning', () => {
    const nodes = [
      aNode({
        path: 'anexo:2',
        kind: 'annex',
        label: '2',
        parent_path: null,
        current: { ...aReadingUnit().nodes[0]!.current, text: 'Tabla de infracciones '.repeat(50) },
        warnings: [{ code: 'annex_table_unstructured', message: 'Este anexo es una tabla.' }],
      }),
    ];
    const { el } = render({ nodes });

    const region = el.querySelector('.annex-text');
    expect(region?.getAttribute('role')).toBe('region');
    expect(region?.getAttribute('aria-label')).toBe('Texto del Anexo 2');
    expect(text(el.querySelector('.warning'))).toContain('Este anexo es una tabla.');
  });

  it('does not offer PDF actions for a container, which has no text of its own', () => {
    const nodes = [
      aNode({
        path: 'titulo:I',
        kind: 'title',
        label: 'I',
        parent_path: null,
        current: { ...aReadingUnit().nodes[0]!.current, text: '', title: 'Definiciones' },
      }),
    ];
    const { el } = render({ nodes });

    expect(el.querySelector('.see')).toBeNull();
    expect(text(el.querySelector('.locator'))).toBe('Título I');
  });
});
