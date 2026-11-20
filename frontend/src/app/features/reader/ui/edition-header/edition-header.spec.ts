import { registerLocaleData } from '@angular/common';
import localeEsPe from '@angular/common/locales/es-PE';
import { LOCALE_ID } from '@angular/core';
import { TestBed } from '@angular/core/testing';

import { anEdition } from '../../../../testing/reader-fixtures';
import { EditionContext } from '../../../../core/api/models';
import { EditionHeader } from './edition-header';

function render(edition: EditionContext) {
  registerLocaleData(localeEsPe);
  TestBed.configureTestingModule({ providers: [{ provide: LOCALE_ID, useValue: 'es-PE' }] });
  const fixture = TestBed.createComponent(EditionHeader);
  fixture.componentRef.setInput('edition', edition);
  fixture.detectChanges();
  return fixture.nativeElement as HTMLElement;
}

const text = (el: Element | null) => el?.textContent?.replace(/\s+/g, ' ').trim() ?? '';

describe('EditionHeader', () => {
  it('names the norm, the edition and says it is not verified', () => {
    const el = render(anEdition());

    expect(text(el.querySelector('.reference'))).toBe('Ley N.° 27181');
    expect(text(el.querySelector('h1'))).toBe('Ley General de Transporte y Tránsito Terrestre');
    expect(text(el.querySelector('drtc-validity-seal'))).toContain('No verificado');
    expect(text(el.querySelector('.edition-label'))).toContain('Compilación no oficial');
    expect(text(el.querySelector('.meta'))).toBe(
      'Fecha de actualización no declarada · 36 páginas · Aprobación automática de desarrollo: sin revisión humana.',
    );
  });

  it('shows the consolidation date when the edition declares one', () => {
    const el = render(anEdition({ consolidated_as_of: '2017-01-04', approval_mode: 'human' }));

    expect(text(el.querySelector('.meta'))).toBe(
      'Actualizado al 4 de enero de 2017 · 36 páginas · Aprobada por revisión humana.',
    );
  });

  it('keeps the edition warnings available but collapsed', () => {
    const el = render(anEdition());

    const alerts = el.querySelector('details.alerts') as HTMLDetailsElement;
    expect(text(alerts.querySelector('summary'))).toBe('Advertencias de esta edición (1)');
    expect(alerts.open).toBe(false);
    expect(text(alerts.querySelector('li'))).toBe('Modificada después de 2020.');
  });

  it('omits the warnings block when there are none', () => {
    expect(render(anEdition({ alerts: [] })).querySelector('details')).toBeNull();
  });
});
