import { useEffect, useId, useMemo, useState, type CSSProperties } from "react";
import { createPortal } from "react-dom";
import type { FileNode } from "../../types";
import { flattenFileTreePaths } from "../../utils/flattenFileTreePaths";

const overlay: CSSProperties = {
  position: "fixed",
  inset: 0,
  background: "rgba(0,0,0,0.55)",
  zIndex: 10000,
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  padding: 16,
};
const dialog: CSSProperties = {
  background: "#252526",
  border: "1px solid #3c3c3c",
  borderRadius: 6,
  padding: 16,
  maxWidth: 520,
  width: "100%",
  maxHeight: "90vh",
  display: "flex",
  flexDirection: "column",
  gap: 10,
  boxShadow: "0 8px 32px rgba(0,0,0,0.45)",
};
const title: CSSProperties = { margin: 0, fontSize: 14, color: "#e0e0e0", fontWeight: 600 };
const label: CSSProperties = { color: "#9d9d9d", fontSize: 11 };
const textInput: CSSProperties = {
  width: "100%",
  boxSizing: "border-box",
  background: "#3c3c3c",
  color: "#d4d4d4",
  border: "1px solid #555",
  borderRadius: 3,
  padding: "6px 8px",
  fontSize: 12,
  fontFamily: "ui-monospace, monospace",
};
const listBox: CSSProperties = {
  border: "1px solid #3c3c3c",
  borderRadius: 3,
  maxHeight: 200,
  overflowY: "auto",
  fontSize: 11,
  background: "#1e1e1e",
};
const listBtn: CSSProperties = {
  display: "block",
  width: "100%",
  textAlign: "left",
  padding: "6px 8px",
  border: "none",
  borderBottom: "1px solid #2d2d2d",
  background: "transparent",
  color: "#d4d4d4",
  cursor: "pointer",
  fontFamily: "ui-monospace, monospace",
  fontSize: 11,
};
const listBtnActive: CSSProperties = {
  ...listBtn,
  background: "#094771",
  color: "#fff",
};
const row: CSSProperties = { display: "flex", gap: 8, justifyContent: "flex-end", marginTop: 4, flexWrap: "wrap" };
const btn: CSSProperties = {
  padding: "6px 14px",
  fontSize: 12,
  borderRadius: 3,
  cursor: "pointer",
  border: "1px solid #555",
  background: "#3c3c3c",
  color: "#d4d4d4",
};
const btnPrimary: CSSProperties = {
  ...btn,
  background: "#0e639c",
  borderColor: "#0e639c",
  color: "#fff",
};
const btnWarn: CSSProperties = {
  ...btn,
  background: "#8b4513",
  borderColor: "#a0522d",
  color: "#fff",
};
const err: CSSProperties = { color: "#f48771", fontSize: 11, margin: 0 };
const hint: CSSProperties = { color: "#8f8f8f", fontSize: 10, margin: 0, lineHeight: 1.4 };
const confirmPath: CSSProperties = {
  ...textInput,
  wordBreak: "break-all",
  padding: 8,
  marginTop: 4,
};

export function formatSaveScriptError(e: unknown): string {
  if (e instanceof Error) return e.message;
  if (typeof e === "string") return e;
  try {
    return JSON.stringify(e);
  } catch {
    return String(e);
  }
}

export type SaveScriptModalProps = {
  open: boolean;
  onClose: () => void;
  /** Shown when the modal opens; user may change before save. */
  initialPath: string | null;
  fileTree: FileNode[];
  onLoadFileTree: () => Promise<void>;
  isSaving: boolean;
  onSave: (path: string) => Promise<void>;
};

type Phase = "form" | "confirm";
type ConfirmKind = "save" | "override";

export function SaveScriptModal({
  open,
  onClose,
  initialPath,
  fileTree,
  onLoadFileTree,
  isSaving,
  onSave,
}: SaveScriptModalProps) {
  const titleId = useId();
  const confirmTitleId = useId();
  const [path, setPath] = useState("");
  const [listQuery, setListQuery] = useState("");
  const [localError, setLocalError] = useState<string | null>(null);
  const [phase, setPhase] = useState<Phase>("form");
  const [confirmKind, setConfirmKind] = useState<ConfirmKind>("save");
  const [pendingPath, setPendingPath] = useState("");

  const filePaths = useMemo(() => flattenFileTreePaths(fileTree), [fileTree]);
  const filteredPaths = useMemo(() => {
    const q = listQuery.trim().toLowerCase();
    if (!q) return filePaths;
    return filePaths.filter((p) => p.toLowerCase().includes(q));
  }, [filePaths, listQuery]);

  const trimmedOpenFile = initialPath?.trim() ?? "";
  const canOverride = trimmedOpenFile.length > 0;

  useEffect(() => {
    if (!open) return;
    setPath(initialPath?.trim() ?? "");
    setListQuery("");
    setLocalError(null);
    setPhase("form");
    setPendingPath("");
    void onLoadFileTree().catch((e: unknown) => {
      setLocalError(formatSaveScriptError(e));
    });
  }, [open, initialPath, onLoadFileTree]);

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key !== "Escape") return;
      if (phase === "confirm") {
        setPhase("form");
        setLocalError(null);
        return;
      }
      onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose, phase]);

  if (!open) return null;

  const body = typeof document !== "undefined" ? document.body : null;
  if (!body) return null;

  function goConfirmSave() {
    const t = path.trim();
    if (!t) {
      setLocalError("Choose or enter a repo-relative path (e.g. src/foo.py).");
      return;
    }
    setLocalError(null);
    setPendingPath(t);
    setConfirmKind("save");
    setPhase("confirm");
  }

  function goConfirmOverride() {
    if (!canOverride) return;
    setLocalError(null);
    setPath(trimmedOpenFile);
    setPendingPath(trimmedOpenFile);
    setConfirmKind("override");
    setPhase("confirm");
  }

  async function executeConfirmedSave() {
    setLocalError(null);
    if (typeof onSave !== "function") {
      setLocalError("Save handler is not available.");
      return;
    }
    try {
      await onSave(pendingPath);
      onClose();
    } catch (e: unknown) {
      setLocalError(formatSaveScriptError(e));
    }
  }

  if (phase === "confirm") {
    return createPortal(
      <div
        style={overlay}
        role="presentation"
        onMouseDown={(e) => {
          if (e.target === e.currentTarget) {
            setPhase("form");
            setLocalError(null);
          }
        }}
      >
        <div
          role="dialog"
          aria-modal="true"
          aria-labelledby={confirmTitleId}
          style={dialog}
          onMouseDown={(e) => e.stopPropagation()}
        >
          <h2 id={confirmTitleId} style={title}>
            Confirm save
          </h2>
          <p style={hint}>
            {confirmKind === "override"
              ? "You are about to overwrite the file currently open in the editor with the buffer contents."
              : "You are about to write the editor buffer to the path below (existing file contents on the server will be replaced)."}
          </p>
          <div>
            <div style={label}>Path</div>
            <div style={confirmPath} role="status">
              {pendingPath}
            </div>
          </div>
          {localError ? (
            <p style={err} role="alert" aria-live="polite">
              {localError}
            </p>
          ) : null}
          <div style={row}>
            <button
              type="button"
              style={btn}
              onClick={() => {
                setPhase("form");
                setLocalError(null);
              }}
              disabled={isSaving}
            >
              Back
            </button>
            <button
              type="button"
              style={btnPrimary}
              onClick={() => void executeConfirmedSave()}
              disabled={isSaving}
            >
              {isSaving ? "Saving…" : confirmKind === "override" ? "Confirm overwrite" : "Confirm save"}
            </button>
          </div>
        </div>
      </div>,
      body,
    );
  }

  return createPortal(
    <div
      style={overlay}
      role="presentation"
      onMouseDown={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        style={dialog}
        onMouseDown={(e) => e.stopPropagation()}
      >
        <h2 id={titleId} style={title}>
          Save script
        </h2>
        <p style={hint}>
          Writes the current editor buffer to the API path below. Pick a file from the list or edit the path (save as
          another file overwrites that path on the server).
        </p>
        <div>
          <label htmlFor="save-script-path-input" style={label}>
            Destination path
          </label>
          <input
            id="save-script-path-input"
            type="text"
            style={{ ...textInput, marginTop: 4 }}
            value={path}
            onChange={(e) => setPath(e.target.value)}
            placeholder="e.g. src/blobert/animated_slug/spider.py"
            disabled={isSaving}
            autoComplete="off"
            spellCheck={false}
          />
        </div>
        {filePaths.length > 0 ? (
          <div>
            <div style={label}>Filter file list</div>
            <input
              type="search"
              aria-label="Filter project files"
              style={{ ...textInput, marginTop: 4, marginBottom: 6 }}
              value={listQuery}
              onChange={(e) => setListQuery(e.target.value)}
              placeholder="Substring filter…"
              disabled={isSaving}
            />
            <div style={label}>Project files (click to set destination)</div>
            <div style={{ ...listBox, marginTop: 4 }} role="listbox" aria-label="Script files">
              {filteredPaths.length === 0 ? (
                <div style={{ padding: 8, color: "#9d9d9d", fontSize: 11 }}>No paths match the filter.</div>
              ) : (
                filteredPaths.slice(0, 400).map((p) => (
                  <button
                    key={p}
                    type="button"
                    role="option"
                    aria-selected={p === path.trim()}
                    style={p === path.trim() ? listBtnActive : listBtn}
                    disabled={isSaving}
                    onClick={() => setPath(p)}
                  >
                    {p}
                  </button>
                ))
              )}
              {filteredPaths.length > 400 ? (
                <div style={{ padding: 6, color: "#858585", fontSize: 10 }}>Showing first 400 matches — narrow the list filter.</div>
              ) : null}
            </div>
          </div>
        ) : (
          <p style={hint}>File list is empty — open the Files panel once or enter a path manually.</p>
        )}
        {localError ? (
          <p style={err} role="alert" aria-live="polite">
            {localError}
          </p>
        ) : null}
        <div style={row}>
          <button type="button" style={btn} onClick={onClose} disabled={isSaving}>
            Cancel
          </button>
          <button type="button" style={btnWarn} onClick={goConfirmOverride} disabled={isSaving || !canOverride} title={!canOverride ? "Open a file first" : undefined}>
            Override current
          </button>
          <button type="button" style={btnPrimary} onClick={goConfirmSave} disabled={isSaving}>
            Save
          </button>
        </div>
      </div>
    </div>,
    body,
  );
}
