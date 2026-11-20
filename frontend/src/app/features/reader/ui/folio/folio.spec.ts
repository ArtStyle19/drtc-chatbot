import { ComponentFixture, TestBed } from '@angular/core/testing';

import { FakePdfLoader } from '../../../../testing/fake-pdf';
import { PDF_LOADER } from '../../data-access/pdf/pdf-port';
import { FolioTarget } from '../../data-access/reading-tree';
import { Folio } from './folio';

class NoopResizeObserver {
  readonly observe = vi.fn();
  readonly disconnect = vi.fn();
}

const TARGET: FolioTarget = {
  label: 'Ley N.° 27181, art. 2, lit. e)',
  pageStart: 3,
  pageEnd: 4,
  replaced: false,
  boxes: [
    { page: 3, x0: 80, y0: 300, x1: 500, y1: 312 },
    { page: 4, x0: 80, y0: 700, x1: 500, y1: 712 },
  ],
};

async function setup(target: FolioTarget | null = TARGET, loader = new FakePdfLoader()) {
  vi.stubGlobal('ResizeObserver', NoopResizeObserver);
  TestBed.configureTestingModule({ providers: [{ provide: PDF_LOADER, useValue: loader }] });
  const fixture = TestBed.createComponent(Folio);
  fixture.componentRef.setInput('sourceUrl', '/api/v1/versions/ley-27181@2020-05/source');
  fixture.componentRef.setInput('fileName', 'ley-27181.pdf');
  fixture.componentRef.setInput('target', target);
  fixture.detectChanges();
  await settle(fixture);
  return { fixture, loader, el: fixture.nativeElement as HTMLElement };
}

/** Lets the document open and the page render (they are promise chains outside Angular's tasks). */
async function settle(fixture: ComponentFixture<Folio>): Promise<void> {
  for (let i = 0; i < 5; i++) {
    await Promise.resolve();
    fixture.detectChanges();
  }
}

const marks = (el: HTMLElement) => [...el.querySelectorAll<HTMLElement>('.mark')];
const click = (el: HTMLElement, selector: string) =>
  (el.querySelector(selector) as HTMLElement).click();

afterEach(() => vi.unstubAllGlobals());

describe('Folio', () => {
  it('opens the document on the first page of the passage and highlights only that page', async () => {
    const { el, loader } = await setup();

    expect(loader.opened[0]?.url).toBe('/api/v1/versions/ley-27181@2020-05/source');
    expect(loader.opened[0]?.doc.renders.at(-1)?.page).toBe(3);
    expect((el.querySelector('.page-field input') as HTMLInputElement).value).toBe('3');
    expect(marks(el)).toHaveLength(1);
    expect(el.querySelector('canvas')?.getAttribute('aria-label')).toContain(
      'El pasaje citado está resaltado',
    );
  });

  it('places the highlight where the box is on the rendered page', async () => {
    const { el } = await setup();

    const mark = marks(el)[0] as HTMLElement;
    const k = 608 / 595; // 640 fallback width - 2 * 16 padding, rounded to 8
    expect(parseFloat(mark.style.left)).toBeCloseTo(80 * k, 0);
    expect(parseFloat(mark.style.width)).toBeCloseTo(420 * k, 0);
    expect(parseFloat(mark.style.top)).toBeCloseTo((842 - 312) * k, 0);
    expect(mark.getAttribute('aria-hidden')).toBe('true');
  });

  it('says the pages of a passage and jumps between them, highlighting each one', async () => {
    const { el, fixture } = await setup();

    expect(el.querySelector('.passage-pages')?.textContent?.trim()).toBe('pp. 3-4');
    const chips = [...el.querySelectorAll<HTMLElement>('.chip')];
    expect(chips.map((c) => c.textContent?.trim())).toEqual(['3', '4']);
    expect(chips[0]?.getAttribute('aria-pressed')).toBe('true');

    chips[1]?.click();
    await settle(fixture);

    expect(el.querySelector<HTMLElement>('.chip[aria-pressed="true"]')?.textContent?.trim()).toBe(
      '4',
    );
    expect(marks(el)).toHaveLength(1);
    expect(parseFloat(marks(el)[0]!.style.top)).toBeCloseTo((842 - 712) * (608 / 595), 0);
  });

  it('turns pages with the buttons and the number field, never beyond the document', async () => {
    const { el, fixture } = await setup();

    click(el, 'button[aria-label="Página siguiente"]');
    await settle(fixture);
    expect((el.querySelector('.page-field input') as HTMLInputElement).value).toBe('4');

    const input = el.querySelector('.page-field input') as HTMLInputElement;
    input.value = '99';
    input.dispatchEvent(new Event('change'));
    await settle(fixture);
    expect(input.value).toBe('10');
    expect(
      el.querySelector<HTMLButtonElement>('button[aria-label="Página siguiente"]')?.disabled,
    ).toBe(true);

    input.value = '0';
    input.dispatchEvent(new Event('change'));
    await settle(fixture);
    expect(input.value).toBe('1');
    expect(
      el.querySelector<HTMLButtonElement>('button[aria-label="Página anterior"]')?.disabled,
    ).toBe(true);
  });

  it('follows a new passage to its page', async () => {
    const { fixture, el } = await setup();

    fixture.componentRef.setInput('target', {
      ...TARGET,
      pageStart: 8,
      pageEnd: 8,
      boxes: [{ page: 8, x0: 10, y0: 10, x1: 100, y1: 20 }],
    });
    await settle(fixture);

    expect((el.querySelector('.page-field input') as HTMLInputElement).value).toBe('8');
    expect(el.querySelector('.chips')).toBeNull(); // a single page needs no chips
  });

  it('marks a replaced text as no longer in force', async () => {
    const { el } = await setup({ ...TARGET, replaced: true, label: 'Texto anterior' });

    expect(el.querySelector('.badge')?.textContent).toContain('Texto anterior · no vigente');
    expect(marks(el)[0]?.classList.contains('is-replaced')).toBe(true);
  });

  it('shows a hint and no highlight when nothing is selected', async () => {
    const { el } = await setup(null);

    expect(el.querySelector('.passage.hint')?.textContent).toContain('Elija una disposición');
    expect(marks(el)).toHaveLength(0);
  });

  it('re-renders at another width when zooming, and clamps at the limits', async () => {
    const { el, fixture, loader } = await setup();
    const doc = loader.opened[0]!.doc;
    const widthOf = () => doc.renders.at(-1)!.cssWidth;
    const base = widthOf();

    click(el, 'button[aria-label="Acercar"]');
    await settle(fixture);
    expect(widthOf()).toBeGreaterThan(base);

    for (let i = 0; i < 6; i++) click(el, 'button[aria-label="Acercar"]');
    await settle(fixture);
    expect(el.querySelector<HTMLButtonElement>('button[aria-label="Acercar"]')?.disabled).toBe(
      true,
    );
    expect(el.querySelector('.zoom-level')?.textContent?.trim()).toBe('200 %');

    click(el, '.zoom-level');
    await settle(fixture);
    expect(widthOf()).toBe(base);
  });

  it('explains a load failure, keeps the PDF link and recovers on retry', async () => {
    const loader = new FakePdfLoader();
    loader.failNext = true;
    const { el, fixture } = await setup(TARGET, loader);

    expect(el.querySelector('[role="alert"]')?.textContent).toContain('No se pudo cargar el PDF');
    expect(el.querySelector('[role="alert"]')?.textContent).toContain(
      'El texto de la disposición sigue disponible',
    );
    expect(el.querySelector<HTMLAnchorElement>('[role="alert"] a')?.getAttribute('href')).toBe(
      '/api/v1/versions/ley-27181@2020-05/source',
    );

    click(el, '.retry');
    await settle(fixture);

    expect(el.querySelector('[role="alert"]')).toBeNull();
    expect(marks(el)).toHaveLength(1);
  });

  it('opens the PDF in a new tab safely and releases the previous document on a new source', async () => {
    const { el, fixture, loader } = await setup();
    const link = el.querySelector<HTMLAnchorElement>('.open-link')!;
    expect(link.target).toBe('_blank');
    expect(link.rel).toContain('noopener');

    fixture.componentRef.setInput('sourceUrl', '/api/v1/versions/other/source');
    await settle(fixture);

    expect(loader.opened[0]?.doc.destroyed).toBe(true);
    expect(loader.opened[1]?.url).toBe('/api/v1/versions/other/source');
  });
});
