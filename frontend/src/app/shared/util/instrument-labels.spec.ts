import { approvalNote, instrumentReference } from './instrument-labels';

describe('instrument labels', () => {
  it('writes the reference of a norm', () => {
    expect(instrumentReference('ley', '27181')).toBe('Ley N.° 27181');
    expect(instrumentReference('decreto_supremo', '017-2009-MTC')).toBe(
      'Decreto Supremo N.° 017-2009-MTC',
    );
    expect(instrumentReference('texto_unico_ordenado', '27444')).toBe(
      'Texto Único Ordenado N.° 27444',
    );
  });

  it('never presents an automatic approval as human review', () => {
    expect(approvalNote('human')).toBe('Aprobada por revisión humana.');
    expect(approvalNote('auto_dev')).toContain('sin revisión humana');
    expect(approvalNote(null)).toBe('Pendiente de aprobación.');
  });
});
