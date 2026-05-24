import { useEffect, useId, useMemo, useState, type CSSProperties } from "react";
import { createPortal } from "react-dom";
import { ELEMENTS, type ElementId } from "../../constants/elements";
import type { BuildControlDef } from "../../types";
import { COARSE_ZONE_KEYS } from "../../utils/elementColorPalettes";
import {
  builtinElementDefaultOptions,
  resolveElementPalette,
  seedElementDefaultDraftValues,
} from "../../utils/elementPaletteOverrides";
import { coarseZonesWithMaterial, paletteSwatchColors } from "../../utils/studioLookMaterial";
import { createDraftZoneFillBindings } from "../../utils/studioZoneFillBindings";
import {
  STUDIO_INK_MUTED,
  STUDIO_INK_PRIMARY,
  STUDIO_INK_SECONDARY,
  STUDIO_SURFACE_PANEL,
} from "../../styles/studioTokens";
import { StudioZoneMaterialEditor } from "./StudioZoneMaterialEditor";

const overlay: CSSProperties = {
  position: "fixed",
  inset: 0,
  background: "rgba(0,0,0,0.6)",
  zIndex: 10000,
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  padding: 16,
};

const dialog: CSSProperties = {
  background: "#121218",
  border: "1px solid rgba(255,255,255,0.08)",
  borderRadius: 10,
  padding: 16,
  maxWidth: 520,
  width: "100%",
  maxHeight: "min(92vh, 820px)",
  display: "flex",
  flexDirection: "column",
  gap: 12,
  boxShadow: "0 12px 40px rgba(0,0,0,0.55)",
};

const btnBase: CSSProperties = {
  padding: "6px 12px",
  fontSize: 11,
  fontWeight: 600,
  borderRadius: 6,
  cursor: "pointer",
  border: "1px solid rgba(255,255,255,0.08)",
  background: STUDIO_SURFACE_PANEL,
  color: STUDIO_INK_SECONDARY,
};

type Props = {
  open: boolean;
  slug: string;
  elementId: ElementId;
  defs: readonly BuildControlDef[];
  knownDefKeys: ReadonlySet<string>;
  onClose: () => void;
  onSave: (draftValues: Record<string, unknown>) => void;
  onResetBuiltin: () => void;
};

export function ElementPaletteDefaultsModal({
  open,
  slug,
  elementId,
  defs,
  knownDefKeys,
  onClose,
  onSave,
  onResetBuiltin,
}: Props) {
  const titleId = useId();
  const el = ELEMENTS[elementId];
  const [draftValues, setDraftValues] = useState<Record<string, unknown>>({});

  const partZones = useMemo(() => coarseZonesWithMaterial(knownDefKeys), [knownDefKeys]);
  const paletteColors = useMemo(
    () => paletteSwatchColors(resolveElementPalette(elementId)),
    [elementId],
  );

  const bindings = useMemo(
    () => createDraftZoneFillBindings(draftValues, setDraftValues),
    [draftValues],
  );

  useEffect(() => {
    if (open) {
      setDraftValues(seedElementDefaultDraftValues(elementId, knownDefKeys));
    }
  }, [open, elementId, knownDefKeys]);

  if (!open) return null;

  const handleSave = () => {
    onSave(draftValues);
    onClose();
  };

  const handleResetBuiltin = () => {
    setDraftValues(builtinElementDefaultOptions(elementId, knownDefKeys));
    onResetBuiltin();
    onClose();
  };

  return createPortal(
    <div
      style={overlay}
      data-testid="element-palette-defaults-modal-overlay"
      onMouseDown={(ev) => {
        if (ev.target === ev.currentTarget) onClose();
      }}
    >
      <div
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        data-testid="element-palette-defaults-modal"
        style={dialog}
        onMouseDown={(ev) => ev.stopPropagation()}
      >
        <div>
          <h2 id={titleId} style={{ margin: 0, fontSize: 14, fontWeight: 700, color: STUDIO_INK_PRIMARY }}>
            {el.name} defaults
          </h2>
          <p style={{ margin: "6px 0 0", fontSize: 11, color: STUDIO_INK_MUTED, lineHeight: 1.45 }}>
            Finish, background fill, and pattern settings for each body section. Saved in this browser and applied when
            you pick this element.
          </p>
        </div>

        <div
          style={{
            display: "flex",
            flexDirection: "column",
            gap: 12,
            overflowY: "auto",
            flex: 1,
            minHeight: 0,
            paddingRight: 2,
          }}
        >
          {COARSE_ZONE_KEYS.filter((z) => partZones.includes(z)).map((zone) => (
            <StudioZoneMaterialEditor
              key={zone}
              slug={slug}
              zone={zone}
              defs={defs}
              knownDefKeys={knownDefKeys}
              bindings={bindings}
              accentHue={el.hue}
              accentInk={el.ink}
              paletteColors={paletteColors}
            />
          ))}
        </div>

        <div style={{ display: "flex", gap: 8, flexWrap: "wrap", justifyContent: "flex-end" }}>
          <button type="button" style={btnBase} onClick={onClose}>
            Cancel
          </button>
          <button
            type="button"
            style={btnBase}
            data-testid="element-palette-reset-builtin"
            onClick={handleResetBuiltin}
          >
            Reset to built-in
          </button>
          <button
            type="button"
            data-testid="element-palette-save"
            style={{
              ...btnBase,
              background: el.soft,
              border: `1px solid ${el.hue}`,
              color: el.ink,
            }}
            onClick={handleSave}
          >
            Save defaults
          </button>
        </div>
      </div>
    </div>,
    document.body,
  );
}
