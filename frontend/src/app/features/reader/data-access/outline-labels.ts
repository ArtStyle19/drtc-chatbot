import { OutlineEntry } from '../../../core/api/models';

export interface EntryLabel {
  /** Short identifier shown in monospace, e.g. "Art. 2" or "Título IV". */
  readonly prefix: string;
  /** Human title, already in sentence case, or null. */
  readonly title: string | null;
}

const ACCENTED: Record<string, string> = {
  unica: 'Única',
  decima: 'Décima',
  decimo: 'Décimo',
  septima: 'Séptima',
  septimo: 'Séptimo',
  undecima: 'Undécima',
  duodecima: 'Duodécima',
  vigesima: 'Vigésima',
  vigesimo: 'Vigésimo',
};

/** PDFs often set titles in capitals; show them as sentences ("OBJETO Y ALCANCE" → "Objeto y alcance"). */
export function sentenceCase(text: string): string {
  const letters = text.replace(/[^\p{L}]/gu, '');
  if (letters === '' || letters !== letters.toUpperCase() || letters.length < 4) {
    return text;
  }
  const lower = text.toLocaleLowerCase('es');
  return lower.charAt(0).toLocaleUpperCase('es') + lower.slice(1);
}

function ordinal(slug: string): string {
  return slug
    .split('-')
    .map((word, index) => {
      const accented = ACCENTED[word] ?? word;
      return index === 0
        ? accented.charAt(0).toLocaleUpperCase('es') + accented.slice(1)
        : accented;
    })
    .join(' ');
}

function lastKey(path: string): string {
  const last = path.split('/').at(-1) ?? '';
  return last.includes(':') ? last.slice(0, last.indexOf(':')) : '';
}

/** How an outline entry reads in the table of contents and in the reading header. */
export function entryLabel(
  entry: Pick<OutlineEntry, 'kind' | 'label' | 'title' | 'path'>,
): EntryLabel {
  const title = entry.title ? sentenceCase(entry.title) : null;
  switch (entry.kind) {
    case 'article':
      return { prefix: `Art. ${entry.label}`, title };
    case 'title':
      return {
        prefix: entry.label === 'PRELIMINAR' ? 'Título Preliminar' : `Título ${entry.label}`,
        title,
      };
    case 'chapter':
      return { prefix: `Capítulo ${entry.label}`, title };
    case 'annex':
      return { prefix: `Anexo ${entry.label.toLocaleUpperCase('es')}`, title };
    case 'disposition':
      return { prefix: ordinal(entry.label), title };
    case 'section':
      if (lastKey(entry.path) === 'disposiciones') {
        return {
          prefix: `Disposiciones ${(title ?? ordinal(entry.label)).toLocaleLowerCase('es')}`,
          title: null,
        };
      }
      return { prefix: `Sección ${ordinal(entry.label)}`, title };
    default:
      return { prefix: entry.label, title };
  }
}

/** Container kinds: they have children in the outline and are expanded/collapsed, not opened. */
export function isContainerKind(kind: OutlineEntry['kind']): boolean {
  return kind === 'section' || kind === 'title' || kind === 'chapter';
}
