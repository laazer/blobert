export interface FileNode {
  type: "file" | "dir";
  path: string;
  name: string;
  children?: FileNode[];
}

export interface Asset {
  path: string;
  name: string;
  dir: string;
  size: number;
}

export interface TerminalLine {
  id: number;
  text: string;
}

export type RunCmd = "animated" | "player" | "level" | "smart" | "stats" | "test";
