import { OutlineEntry } from '../../../core/api/models';
import { isContainerKind } from './outline-labels';

export interface OutlineNode {
  readonly entry: OutlineEntry;
  readonly children: readonly OutlineNode[];
}

/** Nests the flat, document-ordered outline by `parent_path`. Entries whose parent is unknown are roots. */
export function buildOutlineTree(entries: readonly OutlineEntry[]): readonly OutlineNode[] {
  const known = new Set(entries.map((e) => e.path));
  const childrenOf = new Map<string | null, OutlineEntry[]>();
  for (const entry of entries) {
    const parent = entry.parent_path && known.has(entry.parent_path) ? entry.parent_path : null;
    const siblings = childrenOf.get(parent) ?? [];
    siblings.push(entry);
    childrenOf.set(parent, siblings);
  }
  const build = (entry: OutlineEntry): OutlineNode => ({
    entry,
    children: (childrenOf.get(entry.path) ?? []).map(build),
  });
  return (childrenOf.get(null) ?? []).map(build);
}

/** Paths of every container that must be open to show `path` (its ancestors). */
export function ancestorsOf(entries: readonly OutlineEntry[], path: string): readonly string[] {
  const byPath = new Map(entries.map((e) => [e.path, e] as const));
  const result: string[] = [];
  let current = byPath.get(path)?.parent_path ?? null;
  while (current && byPath.has(current) && !result.includes(current)) {
    result.push(current);
    current = byPath.get(current)?.parent_path ?? null;
  }
  return result;
}

/** The outline entry the reader should mark as current for a requested path (its reading unit). */
export function entryForPath(
  entries: readonly OutlineEntry[],
  path: string | null,
): OutlineEntry | null {
  if (!path) return null;
  const exact = entries.find((e) => e.path === path);
  if (exact) return exact;
  return entries.find((e) => path.startsWith(e.unit_path + '/') || path === e.unit_path) ?? null;
}

export interface Neighbours {
  readonly previous: OutlineEntry | null;
  readonly next: OutlineEntry | null;
}

/**
 * The readable entries (not containers) before and after `path` in document order, so the reader
 * can step through a norm. Containers have no text of their own and are skipped.
 */
export function neighbours(entries: readonly OutlineEntry[], path: string | null): Neighbours {
  const current = entryForPath(entries, path);
  if (!current) return { previous: null, next: null };
  const readable = entries.filter((e) => !isContainerKind(e.kind));
  const index = readable.findIndex((e) => e.path === current.path);
  if (index === -1) {
    // A container: the neighbours are the readable entries around its position in the outline.
    const position = entries.indexOf(current);
    const before = entries.slice(0, position).filter((e) => !isContainerKind(e.kind));
    const after = entries.slice(position + 1).filter((e) => !isContainerKind(e.kind));
    return { previous: before.at(-1) ?? null, next: after[0] ?? null };
  }
  return { previous: readable[index - 1] ?? null, next: readable[index + 1] ?? null };
}
