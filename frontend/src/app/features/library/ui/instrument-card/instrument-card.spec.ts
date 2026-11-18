import { registerLocaleData } from '@angular/common';
import localeEsPe from '@angular/common/locales/es-PE';
import { LOCALE_ID } from '@angular/core';
import { TestBed } from '@angular/core/testing';
import { provideRouter } from '@angular/router';

import { anInstrument } from '../../../../testing/instrument-fixtures';
import { InstrumentCard } from './instrument-card';

describe('InstrumentCard', () => {
  beforeAll(() => registerLocaleData(localeEsPe));

  it('shows the formal reference, title, edition and validity seal', () => {
    TestBed.configureTestingModule({
      providers: [provideRouter([]), { provide: LOCALE_ID, useValue: 'es-PE' }],
    });
    const fixture = TestBed.createComponent(InstrumentCard);
    fixture.componentRef.setInput('instrument', anInstrument());
    fixture.detectChanges();
    const element = fixture.nativeElement as HTMLElement;

    expect(element.querySelector('.reference')?.textContent).toBe('Ley N.° 27181');
    expect(element.querySelector('h2')?.textContent).toContain('Ley General de Transporte');
    expect(element.textContent).toContain('8 de octubre de 1999');
    expect(element.querySelector('drtc-validity-seal')?.textContent).toContain('No verificado');
    expect(element.querySelector('summary')?.textContent).toContain('Advertencias (1)');
  });

  it('says how many provisions were ingested and never calls an approval a verification', () => {
    TestBed.configureTestingModule({
      providers: [provideRouter([]), { provide: LOCALE_ID, useValue: 'es-PE' }],
    });
    const fixture = TestBed.createComponent(InstrumentCard);
    fixture.componentRef.setInput('instrument', anInstrument());
    fixture.detectChanges();
    const text = (fixture.nativeElement as HTMLElement).querySelector('.ingestion')?.textContent;

    expect(text).toContain('259 disposiciones');
    expect(text).toContain('aprobación automática solo de desarrollo');
    expect(text).not.toMatch(/verificad|vigente/i);
  });

  it('offers to read a norm whose edition is approved', () => {
    TestBed.configureTestingModule({
      providers: [provideRouter([]), { provide: LOCALE_ID, useValue: 'es-PE' }],
    });
    const fixture = TestBed.createComponent(InstrumentCard);
    fixture.componentRef.setInput('instrument', anInstrument());
    fixture.detectChanges();

    const link = (fixture.nativeElement as HTMLElement).querySelector<HTMLAnchorElement>('a.read');
    expect(link?.getAttribute('href')).toBe('/biblioteca/ley-27181');
    expect(link?.textContent?.replace(/\s+/g, ' ').trim()).toBe('Leer norma Ley N.° 27181');
  });

  it('does not offer to read a norm that has nothing approved yet', () => {
    TestBed.configureTestingModule({
      providers: [provideRouter([]), { provide: LOCALE_ID, useValue: 'es-PE' }],
    });
    const base = anInstrument();
    const fixture = TestBed.createComponent(InstrumentCard);
    fixture.componentRef.setInput('instrument', {
      ...base,
      current_edition: { ...base.current_edition, approval_status: 'pending', provision_count: 12 },
    });
    fixture.detectChanges();

    expect((fixture.nativeElement as HTMLElement).querySelector('a.read')).toBeNull();
  });
});
