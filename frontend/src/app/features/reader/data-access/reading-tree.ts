import { ReadingNode, TextBox } from '../../../core/api/models';

export interface ReadingTreeNode {
  readonly node: ReadingNode;
  readonly children: readonly ReadingTreeNode[];
}

/** Nests the flat reading nodes (document order) by `parent_path`; the first node is the root. */
export function buildReadingTree(nodes: readonly ReadingNode[]): readonly ReadingTreeNode[] {
  const known = new Set(nodes.map((n) => n.path));
  const childrenOf = new Map<string | null, ReadingNode[]>();
  for (const node of nodes) {
    const parent = node.parent_path && known.has(node.parent_path) ? node.parent_path : null;
    const siblings = childrenOf.get(parent) ?? [];
    siblings.push(node);
    childrenOf.set(parent, siblings);
  }
  const build = (node: ReadingNode): ReadingTreeNode => ({
    node,
    children: (childrenOf.get(node.path) ?? []).map(build),
  });
  return (childrenOf.get(null) ?? []).map(build);
}

/** What the Folio (PDF viewer) shows: a page range and the line boxes to highlight. */
export interface FolioTarget {
  readonly label: string;
  readonly pageStart: number;
  readonly pageEnd: number;
  readonly boxes: readonly TextBox[];
  /** True when the passage is a replaced text (no longer in force). */
  readonly replaced: boolean;
}

function isWithin(path: string, focus: string): boolean {
  return path === focus || path.startsWith(focus + '/');
}

/** The current text of `focus` and of everything below it (a numeral includes its literals). */
export function currentTarget(
  nodes: readonly ReadingNode[],
  focus: string,
  label: string,
): FolioTarget | null {
  const selected = nodes.filter((n) => isWithin(n.path, focus));
  if (selected.length === 0) return null;
  return {
    label,
    pageStart: Math.min(...selected.map((n) => n.current.page_start)),
    pageEnd: Math.max(...selected.map((n) => n.current.page_end)),
    boxes: selected.flatMap((n) => n.current.boxes),
    replaced: false,
  };
}

/** A replaced revision of one node, shown in the PDF at its original place. */
export function historyTarget(
  nodes: readonly ReadingNode[],
  path: string,
  revision: number,
  label: string,
): FolioTarget | null {
  const old = nodes.find((n) => n.path === path)?.history.find((r) => r.revision === revision);
  if (!old) return null;
  return {
    label,
    pageStart: old.page_start,
    pageEnd: old.page_end,
    boxes: old.boxes,
    replaced: true,
  };
}
