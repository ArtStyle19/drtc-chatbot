import { anEntry } from '../../../testing/reader-fixtures';
import { ancestorsOf, buildOutlineTree, entryForPath, neighbours } from './outline-tree';

const ENTRIES = [
  anEntry({
    path: 'titulo:I',
    kind: 'title',
    label: 'I',
    parent_path: null,
    unit_path: 'titulo:I',
  }),
  anEntry({ path: 'articulo:1', label: '1', parent_path: 'titulo:I', unit_path: 'articulo:1' }),
  anEntry({
    path: 'titulo:IV',
    kind: 'title',
    label: 'IV',
    parent_path: null,
    unit_path: 'titulo:IV',
  }),
  anEntry({
    path: 'titulo:IV/capitulo:I',
    kind: 'chapter',
    label: 'I',
    parent_path: 'titulo:IV',
    unit_path: 'titulo:IV/capitulo:I',
  }),
  anEntry({
    path: 'articulo:229',
    label: '229',
    parent_path: 'titulo:IV/capitulo:I',
    unit_path: 'articulo:229',
  }),
  anEntry({ path: 'articulo:36', label: '36', parent_path: null, unit_path: 'articulo:36' }),
];

describe('buildOutlineTree', () => {
  it('nests by parent and keeps document order', () => {
    const tree = buildOutlineTree(ENTRIES);

    expect(tree.map((n) => n.entry.path)).toEqual(['titulo:I', 'titulo:IV', 'articulo:36']);
    expect(tree[0]?.children.map((n) => n.entry.path)).toEqual(['articulo:1']);
    expect(tree[1]?.children[0]?.children.map((n) => n.entry.path)).toEqual(['articulo:229']);
  });

  it('treats entries with an unknown parent as roots instead of dropping them', () => {
    const tree = buildOutlineTree([anEntry({ path: 'articulo:9', parent_path: 'titulo:missing' })]);

    expect(tree.map((n) => n.entry.path)).toEqual(['articulo:9']);
  });
});

describe('ancestorsOf / entryForPath', () => {
  it('lists every container that must be open to show an entry', () => {
    expect(ancestorsOf(ENTRIES, 'articulo:229')).toEqual(['titulo:IV/capitulo:I', 'titulo:IV']);
    expect(ancestorsOf(ENTRIES, 'articulo:36')).toEqual([]);
    expect(ancestorsOf(ENTRIES, 'nope')).toEqual([]);
  });

  it('marks as current the entry whose reading unit contains the requested path', () => {
    expect(entryForPath(ENTRIES, 'articulo:229/numeral:229.1/literal:a')?.path).toBe(
      'articulo:229',
    );
    expect(entryForPath(ENTRIES, 'articulo:1')?.path).toBe('articulo:1');
    expect(entryForPath(ENTRIES, 'articulo:999')).toBeNull();
    expect(entryForPath(ENTRIES, null)).toBeNull();
  });
});

describe('neighbours', () => {
  const entries = [
    anEntry({
      path: 'titulo:I',
      kind: 'title',
      label: 'I',
      parent_path: null,
      unit_path: 'titulo:I',
    }),
    anEntry({ path: 'articulo:1', label: '1', unit_path: 'articulo:1' }),
    anEntry({ path: 'articulo:2', label: '2', unit_path: 'articulo:2' }),
    anEntry({
      path: 'titulo:II',
      kind: 'title',
      label: 'II',
      parent_path: null,
      unit_path: 'titulo:II',
    }),
    anEntry({ path: 'articulo:3', label: '3', parent_path: 'titulo:II', unit_path: 'articulo:3' }),
  ];

  it('steps over containers to the previous and next readable entry', () => {
    expect(neighbours(entries, 'articulo:2')).toEqual({ previous: entries[1], next: entries[4] });
  });

  it('has no previous at the start and no next at the end', () => {
    expect(neighbours(entries, 'articulo:1').previous).toBeNull();
    expect(neighbours(entries, 'articulo:3').next).toBeNull();
  });

  it('works from a path inside an article (a literal)', () => {
    expect(neighbours(entries, 'articulo:2/literal:e').previous?.path).toBe('articulo:1');
  });

  it('works from a container, using its place in the outline', () => {
    expect(neighbours(entries, 'titulo:II')).toEqual({ previous: entries[2], next: entries[4] });
  });

  it('is empty for an unknown or missing path', () => {
    expect(neighbours(entries, 'articulo:99')).toEqual({ previous: null, next: null });
    expect(neighbours(entries, null)).toEqual({ previous: null, next: null });
  });
});
