import { anEntry } from '../../../testing/reader-fixtures';
import { entryLabel, isContainerKind, sentenceCase } from './outline-labels';

describe('sentenceCase', () => {
  it.each([
    ['OBJETO, ALCANCE Y DEFINICIONES', 'Objeto, alcance y definiciones'],
    ['DISPOSICIONES GENERALES', 'Disposiciones generales'],
    ['De las definiciones', 'De las definiciones'],
    ['IV', 'IV'],
    ['ONU', 'ONU'],
    ['', ''],
  ])('turns %j into %j', (input, expected) => {
    expect(sentenceCase(input)).toBe(expected);
  });
});

describe('entryLabel', () => {
  it('writes articles, titles and chapters the way lawyers do', () => {
    expect(entryLabel(anEntry())).toEqual({ prefix: 'Art. 2', title: 'De las definiciones' });
    expect(
      entryLabel(
        anEntry({ kind: 'title', label: 'IV', path: 'titulo:IV', title: 'DEL PROCEDIMIENTO' }),
      ),
    ).toEqual({
      prefix: 'Título IV',
      title: 'Del procedimiento',
    });
    expect(
      entryLabel(
        anEntry({ kind: 'title', label: 'PRELIMINAR', path: 'titulo:PRELIMINAR', title: null }),
      ),
    ).toEqual({
      prefix: 'Título Preliminar',
      title: null,
    });
    expect(
      entryLabel(anEntry({ kind: 'chapter', label: 'II', path: 'titulo:IV/capitulo:II' })).prefix,
    ).toBe('Capítulo II');
  });

  it('names groups of dispositions and dispositions with accented ordinals', () => {
    const group = anEntry({
      kind: 'section',
      label: 'complementarias-finales',
      title: 'Complementarias Finales',
      path: 'seccion:sexta/disposiciones:complementarias-finales',
    });
    expect(entryLabel(group)).toEqual({
      prefix: 'Disposiciones complementarias finales',
      title: null,
    });
    expect(
      entryLabel(
        anEntry({
          kind: 'disposition',
          label: 'decima-primera',
          title: 'De la vigencia',
          path: 'x/decima-primera',
        }),
      ).prefix,
    ).toBe('Décima primera');
    expect(
      entryLabel(anEntry({ kind: 'disposition', label: 'unica', path: 'disposicion:unica' }))
        .prefix,
    ).toBe('Única');
  });

  it('names sections and annexes', () => {
    expect(
      entryLabel(
        anEntry({
          kind: 'section',
          label: 'primera',
          path: 'seccion:primera',
          title: 'DISPOSICIONES GENERALES',
        }),
      ),
    ).toEqual({
      prefix: 'Sección Primera',
      title: 'Disposiciones generales',
    });
    expect(
      entryLabel(
        anEntry({
          kind: 'annex',
          label: '2',
          path: 'anexo:2',
          title: 'TABLA DE INFRACCIONES Y SANCIONES',
        }),
      ),
    ).toEqual({
      prefix: 'Anexo 2',
      title: 'Tabla de infracciones y sanciones',
    });
  });

  it('knows which kinds are expandable containers', () => {
    expect(['section', 'title', 'chapter'].every((k) => isContainerKind(k as never))).toBe(true);
    expect(['article', 'annex', 'disposition'].some((k) => isContainerKind(k as never))).toBe(
      false,
    );
  });
});
