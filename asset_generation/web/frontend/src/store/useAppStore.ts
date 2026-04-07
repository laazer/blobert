import { create } from "zustand";
import { immer } from "zustand/middleware/immer";
import { Asset, FileNode, TerminalLine, RunCmd } from "../types";
import {
  fetchFileTree,
  fetchFileContent,
  saveFileContent,
  fetchAssets,
  fetchEnemies,
} from "../api/client";

export type CommandPanelContext = {
  cmd: RunCmd;
  /** Enemy slug, player color, or level object id — empty when the cmd has no enemy field. */
  enemy: string;
};

let _lineId = 0;

interface AppState {
  // File tree
  fileTree: FileNode[];
  selectedFile: string | null;
  loadFileTree: () => Promise<void>;
  selectFile: (path: string) => Promise<void>;

  /** Mirrors CommandPanel selections for preview-side shortcuts (model/animation nav). */
  commandContext: CommandPanelContext;
  setCommandContext: (ctx: CommandPanelContext) => void;

  /** Animated enemy slugs from GET /api/meta/enemies (fallback defaults in quickSourceNav). */
  animatedEnemySlugs: string[];
  loadAnimatedEnemySlugs: () => Promise<void>;

  // Editor
  /** When false, the center editor column is collapsed (file may still be selected). */
  editorPaneVisible: boolean;
  setEditorPaneVisible: (visible: boolean) => void;
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
  /** Load a GLB by server path (e.g. animated_exports/tar_slug_animated_01.glb). */
  selectAssetByPath: (path: string) => void;
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
    commandContext: { cmd: "animated", enemy: "adhesion_bug" },
    setCommandContext(ctx) {
      set((s) => {
        s.commandContext = ctx;
      });
    },
    animatedEnemySlugs: [
      "adhesion_bug",
      "tar_slug",
      "ember_imp",
      "acid_spitter",
      "claw_crawler",
      "carapace_husk",
    ],
    async loadAnimatedEnemySlugs() {
      try {
        const list = await fetchEnemies();
        if (list.length > 0) {
          set((s) => {
            s.animatedEnemySlugs = list;
          });
        }
      } catch {
        /* keep defaults */
      }
    },
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
        s.editorPaneVisible = true;
      });
    },

    // Editor
    editorPaneVisible: true,
    setEditorPaneVisible(visible) {
      set((s) => {
        s.editorPaneVisible = visible;
      });
    },
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
    selectAssetByPath(path) {
      const url = `/api/assets/${path}?t=${Date.now()}`;
      set((s) => {
        s.activeGlbUrl = url;
        s.availableClips = [];
        s.activeAnimation = "Idle";
        s.isAnimationPaused = false;
      });
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
        get().selectAssetByPath(match.path);
      }
    },
  }))
);
