import { anEntry } from '../../../testing/reader-fixtures';
import { ancestorsOf, buildOutlineTree, entryForPath } from './outline-tree';

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
