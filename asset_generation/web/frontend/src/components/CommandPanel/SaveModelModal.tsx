import { useEffect, useId, useState, type CSSProperties } from "react";
import { createPortal } from "react-dom";
import {
  fetchEnemyFamilySlots,
  fetchModelRegistry,
  patchRegistryEnemyVersion,
  putEnemyFamilySlots,
} from "../../api/client";
import type { ModelRegistryPayload, RegistryEnemyVersion } from "../../types";
import { animatedExportVersionId } from "../../utils/glbVariants";
import { appendSlotIfMissing, replaceSlotAssignment, slotListHasDuplicates } from "../../utils/registrySlotOps";
import { formatSaveScriptError } from "./SaveScriptModal";

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
  display: "flex",
  flexDirection: "column",
  gap: 10,
  boxShadow: "0 8px 32px rgba(0,0,0,0.45)",
};
const title: CSSProperties = { margin: 0, fontSize: 14, color: "#e0e0e0", fontWeight: 600 };
const label: CSSProperties = { color: "#9d9d9d", fontSize: 11 };
const selectStyle: CSSProperties = {
  width: "100%",
  boxSizing: "border-box",
  background: "#3c3c3c",
  color: "#d4d4d4",
  border: "1px solid #555",
  borderRadius: 3,
  padding: "6px 8px",
  fontSize: 12,
  marginTop: 4,
};
const row: CSSProperties = { display: "flex", flexDirection: "column", gap: 6 };
const btnRow: CSSProperties = { display: "flex", gap: 8, flexWrap: "wrap", marginTop: 4 };
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
const err: CSSProperties = { color: "#f48771", fontSize: 11, margin: 0 };
const hint: CSSProperties = { color: "#8f8f8f", fontSize: 10, margin: 0, lineHeight: 1.4 };
const mono: CSSProperties = { fontFamily: "ui-monospace, monospace", fontSize: 11, color: "#d4d4d4" };
const textInput: CSSProperties = {
  width: "100%",
  boxSizing: "border-box",
  background: "#3c3c3c",
  color: "#d4d4d4",
  border: "1px solid #555",
  borderRadius: 3,
  padding: "6px 8px",
  fontSize: 12,
  marginTop: 4,
};

const MAX_VERSION_NAME_LEN = 128;

function findVersion(registry: ModelRegistryPayload, family: string, versionId: string): RegistryEnemyVersion | null {
  const versions = registry.enemies[family]?.versions ?? [];
  return versions.find((v) => v.id === versionId) ?? null;
}

function slotErrorForPut(row: RegistryEnemyVersion | null, versionId: string): string | null {
  if (!row) {
    return `Version ${versionId} is not in the registry yet. Run a successful export first, then refresh the Registry tab.`;
  }
  if (row.draft) {
    return "This version is still a draft. Turn off draft in the Registry tab before assigning slots.";
  }
  if (!row.in_use) {
    return "This version must be in the spawn pool (in_use) before it can be slotted.";
  }
  return null;
}

function namePatchIfChanged(trimmedInput: string, previousStored: string | undefined): { name: string | null } | null {
  const prev = (previousStored ?? "").trim();
  if (trimmedInput === prev) return null;
  return { name: trimmedInput === "" ? null : trimmedInput };
}

export type SaveModelModalProps = {
  open: boolean;
  onClose: () => void;
  /** Normalized enemy family slug (e.g. ``spider``). */
  family: string;
  /** GLB variant index; preview / default export uses ``0``. */
  variantIndex?: number;
};

export function SaveModelModal({ open, onClose, family, variantIndex = 0 }: SaveModelModalProps) {
  const titleId = useId();
  const [slotIds, setSlotIds] = useState<string[]>([]);
  const [slotIndex, setSlotIndex] = useState(0);
  const [versionName, setVersionName] = useState("");
  const [localError, setLocalError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(null);

  const versionId = animatedExportVersionId(family, variantIndex);

  useEffect(() => {
    if (!open) return;
    setLocalError(null);
    setLoadError(null);
    setSlotIndex(0);
    let cancelled = false;
    void (async () => {
      try {
        const [payload, registry] = await Promise.all([fetchEnemyFamilySlots(family), fetchModelRegistry()]);
        if (cancelled) return;
        setSlotIds([...payload.version_ids]);
        const row = findVersion(registry, family, versionId);
        setVersionName(row?.name ?? "");
      } catch (e: unknown) {
        if (!cancelled) setLoadError(formatSaveScriptError(e));
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [open, family, versionId]);

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  if (!open) return null;
  const body = typeof document !== "undefined" ? document.body : null;
  if (!body) return null;

  const slotOptionsCount = Math.max(1, slotIds.length);

  async function run(op: "slot" | "new_slot" | "draft") {
    setLocalError(null);
    const nameTrim = versionName.trim();
    if (nameTrim.length > MAX_VERSION_NAME_LEN) {
      setLocalError(`Name must be at most ${MAX_VERSION_NAME_LEN} characters.`);
      return;
    }
    setBusy(true);
    try {
      const registry = await fetchModelRegistry();
      const row = findVersion(registry, family, versionId);
      const namePatch = namePatchIfChanged(nameTrim, row?.name);

      if (op === "draft") {
        if (!row) {
          setLocalError(
            `Version ${versionId} is not in the registry yet. Run a successful export first, then refresh the Registry tab.`,
          );
          return;
        }
        const body: { draft: boolean; in_use: boolean; name?: string | null } = { draft: true, in_use: false };
        if (namePatch) Object.assign(body, namePatch);
        await patchRegistryEnemyVersion(family, versionId, body);
        onClose();
        return;
      }

      const slotErr = slotErrorForPut(row, versionId);
      if (slotErr) {
        setLocalError(slotErr);
        return;
      }

      if (op === "slot") {
        const next = replaceSlotAssignment(slotIds, slotIndex, versionId);
        if (slotListHasDuplicates(next)) {
          setLocalError(
            "That would list the same version twice in slots. Remove the other slot assignment in the Registry tab first.",
          );
          return;
        }
        await putEnemyFamilySlots(family, next);
        if (namePatch) await patchRegistryEnemyVersion(family, versionId, namePatch);
        onClose();
        return;
      }

      const next = appendSlotIfMissing(slotIds, versionId);
      if (next.length === slotIds.length && slotIds.includes(versionId)) {
        setLocalError("This version is already in the slot list.");
        return;
      }
      await putEnemyFamilySlots(family, next);
      if (namePatch) await patchRegistryEnemyVersion(family, versionId, namePatch);
      onClose();
    } catch (e: unknown) {
      setLocalError(formatSaveScriptError(e));
    } finally {
      setBusy(false);
    }
  }

  async function runSaveNameOnly() {
    setLocalError(null);
    const nameTrim = versionName.trim();
    if (nameTrim.length > MAX_VERSION_NAME_LEN) {
      setLocalError(`Name must be at most ${MAX_VERSION_NAME_LEN} characters.`);
      return;
    }
    setBusy(true);
    try {
      const registry = await fetchModelRegistry();
      const row = findVersion(registry, family, versionId);
      if (!row) {
        setLocalError(
          `Version ${versionId} is not in the registry yet. Run a successful export first, then refresh the Registry tab.`,
        );
        return;
      }
      const namePatch = namePatchIfChanged(nameTrim, row.name);
      if (!namePatch) {
        setLocalError("No change to the name.");
        return;
      }
      await patchRegistryEnemyVersion(family, versionId, namePatch);
      onClose();
    } catch (e: unknown) {
      setLocalError(formatSaveScriptError(e));
    } finally {
      setBusy(false);
    }
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
          Save model
        </h2>
        <p style={hint}>
          Updates <span style={mono}>model_registry.json</span> for this family&apos;s default export ({versionId}). Export
          the GLB first so the registry row exists.
        </p>
        {loadError ? (
          <p style={err} role="alert">
            {loadError}
          </p>
        ) : null}
        <div style={row}>
          <label htmlFor="save-model-version-name" style={label}>
            Version name (optional)
          </label>
          <input
            id="save-model-version-name"
            type="text"
            style={textInput}
            value={versionName}
            onChange={(e) => setVersionName(e.target.value)}
            placeholder="e.g. Jungle variant"
            maxLength={MAX_VERSION_NAME_LEN}
            disabled={busy || !!loadError}
            autoComplete="off"
            spellCheck
          />
        </div>
        <div style={row}>
          <label htmlFor="save-model-slot-select" style={label}>
            Slot to set (save in slot)
          </label>
          <select
            id="save-model-slot-select"
            style={selectStyle}
            value={Math.min(slotIndex, Math.max(0, slotOptionsCount - 1))}
            onChange={(e) => setSlotIndex(Number(e.target.value))}
            disabled={busy || !!loadError}
          >
            {Array.from({ length: slotOptionsCount }, (_, i) => {
              const currentId = slotIds[i] ?? "(empty)";
              return (
                <option key={i} value={i}>
                  Slot {i + 1}: {currentId}
                </option>
              );
            })}
          </select>
        </div>
        {localError ? (
          <p style={err} role="alert" aria-live="polite">
            {localError}
          </p>
        ) : null}
        <div style={btnRow}>
          <button type="button" style={btn} onClick={onClose} disabled={busy}>
            Cancel
          </button>
          <button
            type="button"
            style={btn}
            onClick={() => void runSaveNameOnly()}
            disabled={busy || !!loadError}
          >
            Save name
          </button>
          <button
            type="button"
            style={btnPrimary}
            onClick={() => void run("slot")}
            disabled={busy || !!loadError}
          >
            {busy ? "Saving…" : "Save in slot"}
          </button>
          <button
            type="button"
            style={btnPrimary}
            onClick={() => void run("new_slot")}
            disabled={busy || !!loadError}
          >
            Save in new slot
          </button>
          <button
            type="button"
            style={btn}
            onClick={() => void run("draft")}
            disabled={busy || !!loadError}
          >
            Save as draft
          </button>
        </div>
      </div>
    </div>,
    body,
  );
}
