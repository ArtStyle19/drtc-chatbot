import { aNode, aReadingUnit } from '../../../testing/reader-fixtures';
import { buildReadingTree, currentTarget, historyTarget } from './reading-tree';

describe('buildReadingTree', () => {
  it('nests literals under their article', () => {
    const [root] = buildReadingTree(aReadingUnit().nodes);

    expect(root?.node.path).toBe('articulo:2');
    expect(root?.children.map((c) => c.node.path)).toEqual([
      'articulo:2/literal:a',
      'articulo:2/literal:e',
    ]);
  });

  it('makes a node whose parent is not in the unit a root', () => {
    expect(buildReadingTree([aNode({ parent_path: 'titulo:I' })])).toHaveLength(1);
  });
});

describe('currentTarget', () => {
  const nodes = aReadingUnit().nodes;

  it('highlights only the chosen literal, with its own pages', () => {
    const target = currentTarget(nodes, 'articulo:2/literal:e', 'Art. 2, lit. e)');

    expect(target).toMatchObject({
      pageStart: 3,
      pageEnd: 4,
      replaced: false,
      label: 'Art. 2, lit. e)',
    });
    expect(target?.boxes.map((b) => b.page)).toEqual([3, 4]);
  });

  it('highlights the article and everything below it when the article is chosen', () => {
    const target = currentTarget(nodes, 'articulo:2', 'Art. 2');

    expect(target?.boxes).toHaveLength(4); // article + literal a + two lines of literal e
    expect(target).toMatchObject({ pageStart: 3, pageEnd: 4 });
  });

  it('is null for a path that is not in the unit', () => {
    expect(currentTarget(nodes, 'articulo:9', 'x')).toBeNull();
  });
});

describe('historyTarget', () => {
  it('points at the replaced text where it sits in the original PDF', () => {
    const target = historyTarget(aReadingUnit().nodes, 'articulo:2', 1, 'Art. 2 (texto anterior)');

    expect(target).toMatchObject({ pageStart: 2, pageEnd: 2, replaced: true });
    expect(target?.boxes[0]?.page).toBe(2);
  });

  it('is null for unknown revisions', () => {
    expect(historyTarget(aReadingUnit().nodes, 'articulo:2', 7, 'x')).toBeNull();
  });
});
