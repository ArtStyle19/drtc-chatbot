import { EditorialNote, LegalEvent, ReadingNode } from '../../../core/api/models';
import { entryLabel } from './outline-labels';

/** The short identifier of a node in the reading view: "Artículo 2", "2.1", "e)", "Anexo 2"… */
export function nodeLocator(
  node: Pick<ReadingNode, 'kind' | 'label' | 'path' | 'current'>,
): string {
  switch (node.kind) {
    case 'article':
      return `Artículo ${node.label}`;
    case 'numeral':
      return node.label;
    case 'literal':
      return `${node.label})`;
    default:
      return entryLabel({
        kind: node.kind,
        label: node.label,
        path: node.path,
        title: node.current.title,
      }).prefix;
  }
}

const EVENT_VERB: Record<LegalEvent['kind'], string> = {
  substituted: 'Texto modificado por',
  incorporated: 'Incorporado por',
  modified: 'Modificado por',
  repealed: 'Derogado por',
};

/** "Texto modificado por el Decreto de Urgencia Nº 019-2020" (the date is formatted by the template). */
export function eventVerb(event: LegalEvent): string {
  return EVENT_VERB[event.kind];
}

const NOTE_KIND: Record<string, string> = {
  amendment: 'Nota de modificación',
  concordance: 'Concordancias',
  footnote: 'Nota al pie',
  preamble: 'Preámbulo',
  epilogue: 'Cierre',
};

export function noteKindLabel(note: Pick<EditorialNote, 'kind'>): string {
  return NOTE_KIND[note.kind] ?? 'Nota editorial';
}

/** DOM id of a provision in the reading view; the page scrolls to it when a passage is chosen. */
export function provisionAnchor(path: string): string {
  return `p-${path.replace(/[^A-Za-z0-9_-]/g, '_')}`;
}
