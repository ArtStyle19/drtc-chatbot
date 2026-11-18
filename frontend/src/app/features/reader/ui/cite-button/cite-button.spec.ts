import { LiveAnnouncer } from '@angular/cdk/a11y';
import { Clipboard } from '@angular/cdk/clipboard';
import { TestBed } from '@angular/core/testing';

import { CiteButton } from './cite-button';

const CITATION = {
  short: 'Ley N.° 27181, art. 2, lit. e)',
  formal:
    'Ley N.° 27181, Ley General…, art. 2, lit. e). Edición: … (edición no verificada frente a la fuente oficial).',
};

function setup(copyResult = true) {
  const copy = vi.fn().mockReturnValue(copyResult);
  const announce = vi.fn().mockResolvedValue(undefined);
  TestBed.configureTestingModule({
    providers: [
      { provide: Clipboard, useValue: { copy } },
      { provide: LiveAnnouncer, useValue: { announce } },
    ],
  });
  const fixture = TestBed.createComponent(CiteButton);
  fixture.componentRef.setInput('citation', CITATION);
  fixture.componentRef.setInput('subject', 'artículo 2, literal e)');
  fixture.detectChanges();
  const el = fixture.nativeElement as HTMLElement;
  const [formal, short] = [...el.querySelectorAll('button')] as HTMLButtonElement[];
  return { fixture, el, copy, announce, formal: formal!, short: short! };
}

describe('CiteButton', () => {
  beforeEach(() => vi.useFakeTimers());
  afterEach(() => vi.useRealTimers());

  it('copies the formal citation written by the server and announces it', () => {
    const { formal, copy, announce, fixture } = setup();

    formal.click();
    fixture.detectChanges();

    expect(copy).toHaveBeenCalledWith(CITATION.formal);
    expect(announce).toHaveBeenCalledWith('Cita formal copiada', 'polite');
    expect(formal.textContent).toContain('Cita copiada');
  });

  it('copies the short citation too', () => {
    const { short, copy, announce, fixture } = setup();

    short.click();
    fixture.detectChanges();

    expect(copy).toHaveBeenCalledWith(CITATION.short);
    expect(announce).toHaveBeenCalledWith('Cita breve copiada', 'polite');
    expect(short.textContent).toContain('Copiada');
  });

  it('goes back to normal after a moment', () => {
    const { formal, fixture } = setup();

    formal.click();
    vi.advanceTimersByTime(2000);
    fixture.detectChanges();

    expect(formal.textContent).toContain('Copiar cita');
  });

  it('tells the person when copying failed instead of pretending it worked', () => {
    const { formal, announce, el, fixture } = setup(false);

    formal.click();
    fixture.detectChanges();

    expect(announce).toHaveBeenCalledWith(
      'No se pudo copiar la cita. Selecciónela manualmente.',
      'polite',
    );
    expect(el.querySelector('[role="status"]')?.textContent).toContain('No se pudo copiar');
    expect(formal.textContent).toContain('Copiar cita');
  });

  it('names what is cited for screen readers', () => {
    const { formal, short } = setup();

    expect(formal.textContent).toContain('formal de artículo 2, literal e)');
    expect(short.textContent).toContain('de artículo 2, literal e)');
  });
});
