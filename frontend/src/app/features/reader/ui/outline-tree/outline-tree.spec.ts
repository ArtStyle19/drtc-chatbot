import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';

import { OutlineEntry } from '../../../../core/api/models';
import { anEntry } from '../../../../testing/reader-fixtures';
import { ancestorsOf, buildOutlineTree } from '../../data-access/outline-tree';
import { OutlineTree } from './outline-tree';

const ENTRIES: OutlineEntry[] = [
  anEntry({
    path: 'titulo:I',
    kind: 'title',
    label: 'I',
    title: 'OBJETO',
    parent_path: null,
    unit_path: 'titulo:I',
  }),
  anEntry({
    path: 'capitulo:I',
    kind: 'chapter',
    label: 'I',
    title: null,
    parent_path: 'titulo:I',
    unit_path: 'capitulo:I',
  }),
  anEntry({
    path: 'articulo:1',
    label: '1',
    title: 'Finalidad',
    parent_path: 'capitulo:I',
    unit_path: 'articulo:1',
  }),
  anEntry({
    path: 'articulo:2',
    label: '2',
    title: 'Definiciones',
    parent_path: 'titulo:I',
    unit_path: 'articulo:2',
  }),
  anEntry({
    path: 'titulo:II',
    kind: 'title',
    label: 'II',
    title: 'REGIMEN',
    parent_path: null,
    unit_path: 'titulo:II',
  }),
  anEntry({
    path: 'articulo:3',
    label: '3',
    title: 'Autoridades',
    parent_path: 'titulo:II',
    unit_path: 'articulo:3',
  }),
];

function setup(currentPath: string | null = null, versionId: string | null = null) {
  TestBed.configureTestingModule({ providers: [provideRouter([])] });
  const fixture = TestBed.createComponent(OutlineTree);
  fixture.componentRef.setInput('nodes', buildOutlineTree(ENTRIES));
  fixture.componentRef.setInput('instrumentId', 'ley-27181');
  fixture.componentRef.setInput('versionId', versionId);
  fixture.componentRef.setInput('currentPath', currentPath);
  fixture.componentRef.setInput('ancestors', currentPath ? ancestorsOf(ENTRIES, currentPath) : []);
  fixture.detectChanges();
  const el = fixture.nativeElement as HTMLElement;
  const links = () => [...el.querySelectorAll<HTMLAnchorElement>('a.entry')];
  const toggles = () => [...el.querySelectorAll<HTMLButtonElement>('button.toggle')];
  return { fixture, el, links, toggles };
}

const text = (el: Element | null | undefined) => el?.textContent?.replace(/\s+/g, ' ').trim() ?? '';

describe('OutlineTree', () => {
  it('shows only the top level at first, with sentence-case titles', () => {
    const { links } = setup();

    expect(links().map((a) => text(a))).toEqual(['Título I Objeto', 'Título II Regimen']);
  });

  it('opens and closes a container, telling assistive technology its state', () => {
    const { fixture, links, toggles } = setup();
    const toggle = toggles()[0]!;
    expect(toggle.getAttribute('aria-expanded')).toBe('false');
    expect(toggle.getAttribute('aria-label')).toBe('Expandir Título I');

    toggle.click();
    fixture.detectChanges();

    expect(toggle.getAttribute('aria-expanded')).toBe('true');
    expect(toggle.getAttribute('aria-label')).toBe('Contraer Título I');
    expect(links().map((a) => text(a))).toEqual([
      'Título I Objeto',
      'Capítulo I',
      'Art. 2 Definiciones',
      'Título II Regimen',
    ]);
    expect(
      document.getElementById(toggle.getAttribute('aria-controls')!) ??
        fixture.nativeElement.querySelector('ul.nested'),
    ).not.toBeNull();

    toggle.click();
    fixture.detectChanges();
    expect(links()).toHaveLength(2);
  });

  it('reveals and marks the current entry, opening every container that holds it', () => {
    const { links } = setup('articulo:1');

    expect(links().map((a) => text(a))).toContain('Art. 1 Finalidad');
    const current = links().filter((a) => a.getAttribute('aria-current') === 'location');
    expect(current.map((a) => text(a))).toEqual(['Art. 1 Finalidad']);
  });

  it('keeps what the person opened when the current entry changes', () => {
    const { fixture, links, toggles } = setup('articulo:3');
    toggles()
      .find((t) => t.getAttribute('aria-label') === 'Expandir Título I')!
      .click();
    fixture.detectChanges();

    fixture.componentRef.setInput('currentPath', 'articulo:3');
    fixture.componentRef.setInput('ancestors', ['titulo:II', 'titulo:I']);
    fixture.detectChanges();

    expect(links().map((a) => text(a))).toEqual(
      expect.arrayContaining(['Capítulo I', 'Art. 3 Autoridades']),
    );
  });

  it('links every entry to its own URL so it can be opened in a new tab', () => {
    const { links } = setup('articulo:1');

    const hrefs = links().map((a) => a.getAttribute('href'));
    expect(hrefs).toContain('/biblioteca/ley-27181?p=articulo:1');
    expect(hrefs).toContain('/biblioteca/ley-27181?p=titulo:II');
  });

  it('keeps the edition in the link when one was chosen', () => {
    const { links } = setup(null, 'ley-27181@2020-05');

    expect(links()[0]!.getAttribute('href')).toBe(
      '/biblioteca/ley-27181?p=titulo:I&v=ley-27181@2020-05',
    );
  });

  it('is a labelled navigation landmark', () => {
    const { el } = setup();

    expect(el.querySelector('nav')?.getAttribute('aria-label')).toBe('Índice de la norma');
  });
});
