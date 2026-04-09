import type { FileNode } from "../types";

/** All file paths under the tree, depth-first (dirs skipped). */
export function flattenFileTreePaths(nodes: readonly FileNode[]): string[] {
  const out: string[] = [];
  function walk(list: readonly FileNode[]) {
    for (const n of list) {
      if (n.type === "file") out.push(n.path);
      else if (n.children?.length) walk(n.children);
    }
  }
  walk(nodes);
  return out;
}
