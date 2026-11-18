import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';

import { anEntry } from '../../../../testing/reader-fixtures';
import { ContainerView } from './container-view';

function render(children: ReturnType<typeof anEntry>[], versionId: string | null = null) {
  TestBed.configureTestingModule({ providers: [provideRouter([])] });
  const fixture = TestBed.createComponent(ContainerView);
  fixture.componentRef.setInput('children', children);
  fixture.componentRef.setInput('instrumentId', 'tuo-ley-27444');
  fixture.componentRef.setInput('versionId', versionId);
  fixture.detectChanges();
  return fixture.nativeElement as HTMLElement;
}

const text = (el: Element | null | undefined) => el?.textContent?.replace(/\s+/g, ' ').trim() ?? '';

describe('ContainerView', () => {
  it('lists what a título contains, each with a link and its page', () => {
    const el = render([
      anEntry({
        path: 'articulo:229',
        label: '229',
        title: 'DEL SILENCIO',
        page_start: 236,
        unit_path: 'articulo:229',
      }),
      anEntry({
        path: 'capitulo:I',
        kind: 'chapter',
        label: 'I',
        title: null,
        page_start: 240,
        unit_path: 'capitulo:I',
      }),
    ]);

    expect(text(el.querySelector('.intro'))).toBe('Contiene 2 elementos:');
    const items = [...el.querySelectorAll<HTMLAnchorElement>('a.item')];
    expect(items.map((a) => text(a))).toEqual([
      'Art. 229 Del silencio p. 236',
      'Capítulo I p. 240',
    ]);
    expect(items[0]!.getAttribute('href')).toBe('/biblioteca/tuo-ley-27444?p=articulo:229');
  });

  it('uses the singular for one element and keeps the chosen edition', () => {
    const el = render([anEntry({ path: 'articulo:1', unit_path: 'articulo:1' })], 'v1');

    expect(text(el.querySelector('.intro'))).toBe('Contiene 1 elemento:');
    expect(el.querySelector('a.item')?.getAttribute('href')).toBe(
      '/biblioteca/tuo-ley-27444?p=articulo:1&v=v1',
    );
  });

  it('says so when a container has nothing indexed', () => {
    const el = render([]);

    expect(text(el.querySelector('.intro'))).toBe(
      'Este apartado no tiene disposiciones propias indexadas.',
    );
    expect(el.querySelector('a')).toBeNull();
  });
});
