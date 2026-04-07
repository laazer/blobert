import { create } from "zustand";
import { immer } from "zustand/middleware/immer";
import {
  AnimatedBuildControlDef,
  AnimatedEnemyMeta,
  Asset,
  FileNode,
  RunCmd,
  TerminalLine,
} from "../types";
import {
  fetchFileTree,
  fetchFileContent,
  saveFileContent,
  fetchAssets,
  fetchEnemyPreviewMeta,
  mergeBuildOptionValues,
} from "../api/client";
import { DEFAULT_ANIMATED_ENEMY_META } from "../utils/enemyDisplay";

export type CommandPanelContext = {
  cmd: RunCmd;
  /** Enemy slug, player color, or level object id — empty when the cmd has no enemy field. */
  enemy: string;
};

/** Center column: code editor and build controls share this space (only one visible at a time; both can be hidden). */
export type CenterPanel = "none" | "code" | "build";

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

  /** Animated enemy slug + label from GET /api/meta/enemies (fallback: enemyDisplay.DEFAULT_ANIMATED_ENEMY_META). */
  animatedEnemyMeta: AnimatedEnemyMeta[];
  /** Procedural build control definitions per slug (from meta API). */
  animatedBuildControls: Record<string, AnimatedBuildControlDef[]>;
  /** Current values per slug for build controls (merged with defaults). */
  animatedBuildOptionValues: Record<string, Record<string, unknown>>;
  setAnimatedBuildOption: (slug: string, key: string, value: unknown) => void;
  /** GET /api/meta/enemies — idle until first load, then ok/error. */
  enemyMetaStatus: "idle" | "loading" | "ok" | "error";
  enemyMetaError: string | null;
  /** From response meta_backend: ok = full Python introspection; fallback = ImportError path. */
  metaBackend: "ok" | "fallback" | null;
  /** Server meta_error when meta_backend is fallback. */
  metaBackendDetail: string | null;
  loadAnimatedEnemyMeta: () => Promise<void>;

  // Editor + build (shared center column)
  centerPanel: CenterPanel;
  setCenterPanel: (panel: CenterPanel) => void;
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
  /** Load a GLB by server path (preview uses paths from `glbVariants.animatedExportRelativePath` for animated enemies). */
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
    commandContext: { cmd: "animated", enemy: "spider" },
    setCommandContext(ctx) {
      set((s) => {
        s.commandContext = ctx;
      });
    },
    animatedEnemyMeta: DEFAULT_ANIMATED_ENEMY_META,
    animatedBuildControls: {},
    animatedBuildOptionValues: {},
    enemyMetaStatus: "idle",
    enemyMetaError: null,
    metaBackend: null,
    metaBackendDetail: null,
    setAnimatedBuildOption(slug, key, value) {
      set((s) => {
        const cur = s.animatedBuildOptionValues[slug] ?? {};
        s.animatedBuildOptionValues[slug] = { ...cur, [key]: value };
      });
    },
    async loadAnimatedEnemyMeta() {
      set((s) => {
        s.enemyMetaStatus = "loading";
        s.enemyMetaError = null;
        s.metaBackend = null;
        s.metaBackendDetail = null;
      });
      try {
        const meta = await fetchEnemyPreviewMeta();
        set((s) => {
          if (meta.enemies.length > 0) {
            s.animatedEnemyMeta = meta.enemies;
          }
          s.animatedBuildControls = meta.animatedBuildControls;
          s.animatedBuildOptionValues = mergeBuildOptionValues(
            meta.animatedBuildControls,
            s.animatedBuildOptionValues,
          );
          s.enemyMetaStatus = "ok";
          s.enemyMetaError = null;
          s.metaBackend = meta.metaBackend ?? "ok";
          s.metaBackendDetail = meta.metaError ?? null;
        });
      } catch (e) {
        const message = e instanceof Error ? e.message : "Failed to load enemy meta.";
        set((s) => {
          s.enemyMetaStatus = "error";
          s.enemyMetaError = message;
          s.metaBackend = null;
          s.metaBackendDetail = null;
        });
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
        s.centerPanel = "code";
      });
    },

    centerPanel: "code",
    setCenterPanel(panel) {
      set((s) => {
        s.centerPanel = panel;
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
      const normalized = outputFile.includes("/") ? outputFile : `animated_exports/${outputFile}`;
      const basename = normalized.split("/").pop() ?? "";
      get().selectAssetByPath(normalized);
    },
  }))
);
