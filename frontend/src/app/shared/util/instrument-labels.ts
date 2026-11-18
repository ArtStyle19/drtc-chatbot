import { InstrumentType } from '../../core/api/models';

export const INSTRUMENT_TYPE_LABELS: Record<InstrumentType, string> = {
  ley: 'Ley',
  decreto_supremo: 'Decreto Supremo',
  decreto_legislativo: 'Decreto Legislativo',
  decreto_de_urgencia: 'Decreto de Urgencia',
  texto_unico_ordenado: 'Texto Único Ordenado',
  reglamento: 'Reglamento',
  resolucion: 'Resolución',
  ordenanza_regional: 'Ordenanza Regional',
  otro: 'Norma',
};

/** "Ley N.° 27181", "Decreto Supremo N.° 017-2009-MTC". */
export function instrumentReference(type: InstrumentType, number: string): string {
  return `${INSTRUMENT_TYPE_LABELS[type]} N.° ${number}`;
}

/** What the approval of an edition means: an approval is NOT a verification of its validity. */
export function approvalNote(mode: 'human' | 'auto_dev' | null): string {
  if (mode === 'human') return 'Aprobada por revisión humana.';
  if (mode === 'auto_dev') return 'Aprobación automática de desarrollo: sin revisión humana.';
  return 'Pendiente de aprobación.';
}
