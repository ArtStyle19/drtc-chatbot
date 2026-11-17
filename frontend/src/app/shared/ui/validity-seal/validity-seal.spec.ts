import { TestBed } from '@angular/core/testing';

import { VerificationStatus } from '../../../core/api/models';
import { ValiditySeal } from './validity-seal';

function render(status: VerificationStatus, edition: string | null = null): HTMLElement {
  const fixture = TestBed.createComponent(ValiditySeal);
  fixture.componentRef.setInput('status', status);
  fixture.componentRef.setInput('edition', edition);
  fixture.detectChanges();
  return fixture.nativeElement as HTMLElement;
}

describe('ValiditySeal', () => {
  it.each<[VerificationStatus, string, string]>([
    ['verified_current', 'Vigente verificado', 'verified'],
    ['unverified', 'No verificado', 'unverified'],
    ['pending_review', 'En revisión', 'unverified'],
    ['superseded', 'Sustituido', 'superseded'],
    ['repealed', 'Derogado', 'repealed'],
    ['unknown', 'Vigencia desconocida', 'superseded'],
  ])('shows %s as "%s"', (status, label, tone) => {
    const element = render(status);

    expect(element.querySelector('.seal-label')?.textContent).toBe(label);
    expect(element.getAttribute('data-tone')).toBe(tone);
  });

  it('never words an unverified text as current', () => {
    const element = render('unverified');

    expect(element.textContent).not.toMatch(/vigente verificado/i);
    expect(element.textContent).toContain('no se presenta como vigente');
  });

  it('appends the edition when given', () => {
    expect(render('unverified', 'edición 04.01.2017').textContent).toContain('edición 04.01.2017');
  });
});
