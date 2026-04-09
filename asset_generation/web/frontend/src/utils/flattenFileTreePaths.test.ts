import { describe, expect, it } from "vitest";
import type { FileNode } from "../types";
import { flattenFileTreePaths } from "./flattenFileTreePaths";

describe("flattenFileTreePaths", () => {
  it("returns empty for empty tree", () => {
    expect(flattenFileTreePaths([])).toEqual([]);
  });

  it("collects nested files in order", () => {
    const tree: FileNode[] = [
      {
        type: "dir",
        path: "a",
        name: "a",
        children: [
          { type: "file", path: "a/x.py", name: "x.py" },
          { type: "file", path: "a/y.py", name: "y.py" },
        ],
      },
      { type: "file", path: "root.py", name: "root.py" },
    ];
    expect(flattenFileTreePaths(tree)).toEqual(["a/x.py", "a/y.py", "root.py"]);
  });
});
