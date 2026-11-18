import { aNode } from '../../../testing/reader-fixtures';
import { eventVerb, nodeLocator, noteKindLabel, provisionAnchor } from './provision-labels';

describe('nodeLocator', () => {
  it.each([
    [{ kind: 'article', label: '2' }, 'Artículo 2'],
    [{ kind: 'article', label: '4-A' }, 'Artículo 4-A'],
    [{ kind: 'numeral', label: '218.2' }, '218.2'],
    [{ kind: 'literal', label: 'e' }, 'e)'],
    [{ kind: 'annex', label: '2', path: 'anexo:2' }, 'Anexo 2'],
    [{ kind: 'disposition', label: 'tercera', path: 'disposiciones:finales/tercera' }, 'Tercera'],
  ])('writes %j as %j', (overrides, expected) => {
    expect(nodeLocator(aNode(overrides as never))).toBe(expected);
  });
});

describe('labels of events and notes', () => {
  it('words each kind of legal event', () => {
    expect(eventVerb({ kind: 'substituted', source: 'x', published_on: null })).toBe(
      'Texto modificado por',
    );
    expect(eventVerb({ kind: 'incorporated', source: 'x', published_on: null })).toBe(
      'Incorporado por',
    );
    expect(eventVerb({ kind: 'repealed', source: 'x', published_on: null })).toBe('Derogado por');
  });

  it('names editorial notes and falls back for unknown kinds', () => {
    expect(noteKindLabel({ kind: 'concordance' })).toBe('Concordancias');
    expect(noteKindLabel({ kind: 'amendment' })).toBe('Nota de modificación');
    expect(noteKindLabel({ kind: 'something-new' })).toBe('Nota editorial');
  });
});

describe('provisionAnchor', () => {
  it('makes a safe DOM id out of a structural path', () => {
    expect(provisionAnchor('articulo:2/literal:e')).toBe('p-articulo_2_literal_e');
    expect(provisionAnchor('articulo:218/numeral:218.2')).toBe('p-articulo_218_numeral_218_2');
  });
});
