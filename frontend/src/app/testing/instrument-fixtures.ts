import { LegalInstrument } from '../core/api/models';

/** Builds a LegalInstrument as returned by GET /api/v1/instruments. */
export function anInstrument(overrides: Partial<LegalInstrument> = {}): LegalInstrument {
  return {
    id: 'ley-27181',
    type: 'ley',
    number: '27181',
    title: 'Ley General de Transporte y Tránsito Terrestre',
    short_name: 'Ley 27181 (LGTTT)',
    issuing_authority: 'Congreso de la República',
    publication_date: '1999-10-08',
    version_count: 1,
    current_edition: {
      version_id: 'ley-27181@2020-05',
      edition_label: 'Compilación no oficial con modificaciones hasta mayo de 2020',
      consolidated_as_of: null,
      verification_status: 'unverified',
      may_be_presented_as_current: false,
      page_count: 36,
      alerts: ['Modificada después de 2020.'],
      approval_status: 'approved',
      approval_mode: 'auto_dev',
      provision_count: 259,
    },
    ...overrides,
  };
}
