import {
  EditionContext,
  OutlineEntry,
  ReadingNode,
  ReadingRevision,
  ReadingUnit,
} from '../core/api/models';

export function anEdition(overrides: Partial<EditionContext> = {}): EditionContext {
  return {
    instrument_id: 'ley-27181',
    type: 'ley',
    number: '27181',
    title: 'Ley General de Transporte y Tránsito Terrestre',
    short_name: 'Ley 27181 (LGTTT)',
    version_id: 'ley-27181@2020-05',
    edition_label: 'Compilación no oficial con modificaciones hasta mayo de 2020',
    consolidated_as_of: null,
    verification_status: 'unverified',
    may_be_presented_as_current: false,
    approval_mode: 'auto_dev',
    page_count: 36,
    alerts: ['Modificada después de 2020.'],
    source_url: '/api/v1/versions/ley-27181@2020-05/source',
    ...overrides,
  };
}

export function anEntry(overrides: Partial<OutlineEntry> = {}): OutlineEntry {
  return {
    path: 'articulo:2',
    kind: 'article',
    label: '2',
    title: 'De las definiciones',
    parent_path: 'titulo:I',
    page_start: 2,
    unit_path: 'articulo:2',
    ...overrides,
  };
}

export function aRevision(overrides: Partial<ReadingRevision> = {}): ReadingRevision {
  return {
    revision: 1,
    title: null,
    text: 'Texto vigente.',
    page_start: 3,
    page_end: 3,
    boxes: [{ page: 3, x0: 80, y0: 600, x1: 500, y1: 612 }],
    event: null,
    citation: {
      short: 'Ley N.° 27181, art. 2',
      formal: 'Ley N.° 27181, … (edición no verificada).',
    },
    ...overrides,
  };
}

export function aNode(overrides: Partial<ReadingNode> = {}): ReadingNode {
  return {
    path: 'articulo:2',
    kind: 'article',
    label: '2',
    parent_path: 'titulo:I',
    revision_count: 1,
    current: aRevision({ title: 'De las definiciones' }),
    history: [],
    warnings: [],
    notes: [],
    ...overrides,
  };
}

/** Article 2 replaced once (history), with literals a and e, as in the real Ley 27181. */
export function aReadingUnit(overrides: Partial<ReadingUnit> = {}): ReadingUnit {
  const event = {
    kind: 'substituted',
    source: 'el Decreto de Urgencia Nº 019-2020',
    published_on: '2020-01-24',
  } as const;
  return {
    edition: anEdition(),
    requested_path: 'articulo:2',
    unit_path: 'articulo:2',
    nodes: [
      aNode({
        revision_count: 2,
        current: aRevision({
          revision: 2,
          title: 'De las definiciones',
          text: 'Para efectos de la presente Ley, entiéndase por:',
          event,
        }),
        history: [
          aRevision({
            revision: 1,
            page_start: 2,
            page_end: 2,
            text: 'Texto anterior del artículo.',
            boxes: [{ page: 2, x0: 80, y0: 400, x1: 500, y1: 412 }],
            citation: {
              short: 'Ley N.° 27181, art. 2 (texto sustituido)',
              formal: '… Texto sustituido por …: no vigente.',
            },
          }),
        ],
        notes: [
          { kind: 'amendment', text: '(**) Artículo modificado por el DU 019-2020.', page: 3 },
        ],
      }),
      aNode({
        path: 'articulo:2/literal:a',
        kind: 'literal',
        label: 'a',
        parent_path: 'articulo:2',
        current: aRevision({
          text: 'Entidad Complementaria: persona natural o jurídica.',
          boxes: [{ page: 3, x0: 80, y0: 560, x1: 500, y1: 572 }],
        }),
      }),
      aNode({
        path: 'articulo:2/literal:e',
        kind: 'literal',
        label: 'e',
        parent_path: 'articulo:2',
        current: aRevision({
          text: 'Servicio de Transporte de Personas.',
          page_start: 3,
          page_end: 4,
          boxes: [
            { page: 3, x0: 80, y0: 300, x1: 500, y1: 312 },
            { page: 4, x0: 80, y0: 700, x1: 500, y1: 712 },
          ],
          citation: {
            short: 'Ley N.° 27181, art. 2, lit. e)',
            formal: 'Ley N.° 27181, …, art. 2, lit. e). Edición: … (edición no verificada).',
          },
        }),
        warnings: [
          {
            code: 'paragraph_replacement_unapplied',
            message: 'Una norma posterior sustituyó un párrafo de esta disposición.',
          },
        ],
      }),
    ],
    children: [],
    ...overrides,
  };
}
