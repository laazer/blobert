import { create } from "zustand";
import { immer } from "zustand/middleware/immer";
import { Asset, FileNode, TerminalLine, RunCmd } from "../types";
import {
  fetchFileTree,
  fetchFileContent,
  saveFileContent,
  fetchAssets,
} from "../api/client";

let _lineId = 0;

interface AppState {
  // File tree
  fileTree: FileNode[];
  selectedFile: string | null;
  loadFileTree: () => Promise<void>;
  selectFile: (path: string) => Promise<void>;

  // Editor
  editorContent: string;
  isDirty: boolean;
  isSaving: boolean;
  setEditorContent: (content: string) => void;
  saveFile: () => Promise<void>;

  // Run
  isRunning: boolean;
  terminalLines: TerminalLine[];
  setIsRunning: (v: boolean) => void;
  appendLine: (text: string) => void;
  clearTerminal: () => void;

  // Assets
  assets: Asset[];
  activeGlbUrl: string | null;
  availableClips: string[];
  activeAnimation: string | null;
  isAnimationPaused: boolean;
  loadAssets: () => Promise<void>;
  setActiveGlbUrl: (url: string | null) => void;
  setAvailableClips: (names: string[]) => void;
  setActiveAnimation: (name: string | null) => void;
  setIsAnimationPaused: (paused: boolean) => void;
  refreshAssetsAndAutoSelect: (outputFile: string | null) => Promise<void>;
}

export const useAppStore = create<AppState>()(
  immer((set, get) => ({
    // File tree
    fileTree: [],
    selectedFile: null,
    async loadFileTree() {
      const tree = await fetchFileTree();
      set((s) => { s.fileTree = tree; });
    },
    async selectFile(path) {
      const content = await fetchFileContent(path);
      set((s) => {
        s.selectedFile = path;
        s.editorContent = content;
        s.isDirty = false;
      });
    },

    // Editor
    editorContent: "",
    isDirty: false,
    isSaving: false,
    setEditorContent(content) {
      set((s) => {
        s.editorContent = content;
        s.isDirty = true;
      });
    },
    async saveFile() {
      const { selectedFile, editorContent } = get();
      if (!selectedFile) return;
      set((s) => { s.isSaving = true; });
      try {
        await saveFileContent(selectedFile, editorContent);
        set((s) => { s.isDirty = false; });
      } finally {
        set((s) => { s.isSaving = false; });
      }
    },

    // Run
    isRunning: false,
    terminalLines: [],
    setIsRunning(v) {
      set((s) => { s.isRunning = v; });
    },
    appendLine(text) {
      set((s) => {
        s.terminalLines.push({ id: _lineId++, text });
        // Keep last 5000 lines
        if (s.terminalLines.length > 5000) {
          s.terminalLines.splice(0, s.terminalLines.length - 5000);
        }
      });
    },
    clearTerminal() {
      set((s) => { s.terminalLines = []; });
    },

    // Assets
    assets: [],
    activeGlbUrl: null,
    availableClips: [],
    activeAnimation: null,
    isAnimationPaused: false,
    async loadAssets() {
      const assets = await fetchAssets();
      set((s) => { s.assets = assets; });
    },
    setActiveGlbUrl(url) {
      set((s) => { s.activeGlbUrl = url; });
    },
    setAvailableClips(names) {
      set((s) => { s.availableClips = names; });
    },
    setActiveAnimation(name) {
      set((s) => { s.activeAnimation = name; });
    },
    setIsAnimationPaused(paused) {
      set((s) => { s.isAnimationPaused = paused; });
    },
    async refreshAssetsAndAutoSelect(outputFile) {
      const assets = await fetchAssets();
      set((s) => { s.assets = assets; });
      if (!outputFile) return;
      const match = assets.find((a) => a.path === outputFile || a.name === outputFile);
      if (match) {
        const url = `/api/assets/${match.path}?t=${Date.now()}`;
        set((s) => {
          s.activeGlbUrl = url;
          s.availableClips = [];
          s.activeAnimation = "Idle";
          s.isAnimationPaused = false;
        });
      }
    },
  }))
);
