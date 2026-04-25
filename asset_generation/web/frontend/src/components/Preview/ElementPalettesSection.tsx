import { useCallback, useMemo, useState, type CSSProperties } from "react";
import { useAppStore } from "../../store/useAppStore";
import {
  COARSE_ZONE_KEYS,
  DEFAULT_ELEMENT_PALETTES,
  ELEMENT_IDS,
  ELEMENT_LABELS,
  type ElementId,
  buildFeatUpdatesFromPalette,
  defaultElementForSlug,
} from "../../utils/elementColorPalettes";
import { copyHexToClipboard } from "../../utils/clipboardHex";
import { slugDisplayLabel } from "../../utils/enemyDisplay";
import { ZONE_FINISH_HEX_RE } from "./featureMaterialPartition";

const btnPrimary: CSSProperties = {
  padding: "4px 10px",
  fontSize: 11,
  borderRadius: 3,
  cursor: "pointer",
  border: "1px solid #0e639c",
  background: "#0e639c",
  color: "#fff",
};

type Props = { slug: string };

export function ElementPalettesSection({ slug }: Props) {
  const meta = useAppStore((s) => s.animatedEnemyMeta);
  const defs = useAppStore((s) => s.animatedBuildControls[slug] ?? []);
  const values = useAppStore((s) => s.animatedBuildOptionValues[slug] ?? {});
  const applyBulk = useAppStore((s) => s.applyAnimatedBuildOptionsForSlug);

  const knownDefKeys = useMemo(() => {
    const keys = new Set<string>();
    for (const d of defs) {
      keys.add(d.key);
    }
    return keys;
  }, [defs]);

  const [copiedLabel, setCopiedLabel] = useState<string | null>(null);
  const suggested = defaultElementForSlug(slug);

  const copySwatchColor = useCallback(async (hex: string, zone: string) => {
    const ok = await copyHexToClipboard(hex);
    if (ok) {
      setCopiedLabel(`${zone} → ${hex.startsWith("#") ? hex : `#${hex}`}`);
      window.setTimeout(() => setCopiedLabel(null), 1600);
    }
  }, []);

  const applyElement = useCallback(
    (id: ElementId) => {
      const palette = DEFAULT_ELEMENT_PALETTES[id];
      const updates = buildFeatUpdatesFromPalette(palette, knownDefKeys, values);
      if (Object.keys(updates).length === 0) return;
      applyBulk(slug, updates);
    },
    [slug, knownDefKeys, values, applyBulk],
  );

  const hasCoarseZones = defs.some((d) => ZONE_FINISH_HEX_RE.test(d.key));

  return (
    <div
      style={{
        border: "1px solid #3c3c3c",
        borderRadius: 4,
        padding: 10,
        background: "#252526",
        marginBottom: 10,
      }}
    >
      <div style={{ fontSize: 12, fontWeight: 600, color: "#d4d4d4", marginBottom: 4 }}>Element palettes</div>
      <p style={{ color: "#8f8f8f", fontSize: 11, margin: "0 0 8px", lineHeight: 1.45 }}>
        Fixed presets (combat + earth, forest, water, lightning) — not editable here. <strong style={{ color: "#bbb" }}>Apply</strong>{" "}
        sets coarse zone finishes + hexes for this enemy. <strong style={{ color: "#bbb" }}>Click a swatch</strong> to copy{" "}
        <code style={{ color: "#ccc" }}>#RRGGBB</code>. Limb / joint overrides are unchanged.
      </p>
      {copiedLabel ? (
        <p style={{ color: "#89d185", fontSize: 11, margin: "0 0 8px" }} role="status">
          Copied {copiedLabel}
        </p>
      ) : null}
      {suggested ? (
        <p style={{ color: "#b5b5b5", fontSize: 11, margin: "0 0 10px" }}>
          Suggested for <strong style={{ color: "#ddd" }}>{slugDisplayLabel(slug, meta)}</strong>:{" "}
          {ELEMENT_LABELS[suggested]}
        </p>
      ) : null}
      {!hasCoarseZones ? (
        <div style={{ color: "#d7ba7d", fontSize: 11 }}>No coarse zone controls loaded for this enemy yet.</div>
      ) : (
        ELEMENT_IDS.map((id) => {
          const palette = DEFAULT_ELEMENT_PALETTES[id];
          return (
            <div
              key={id}
              style={{
                display: "flex",
                alignItems: "center",
                gap: 8,
                flexWrap: "wrap",
                marginBottom: 8,
                paddingBottom: 8,
                borderBottom: "1px solid #2d2d2d",
              }}
            >
              <span style={{ minWidth: 84, fontSize: 11, color: "#d4d4d4", fontWeight: 600 }}>{ELEMENT_LABELS[id]}</span>
              <div style={{ display: "flex", gap: 3, alignItems: "center" }}>
                {COARSE_ZONE_KEYS.map((z) => {
                  const hex = palette[z]?.hex;
                  if (!hex) return null;
                  return (
                    <button
                      key={z}
                      type="button"
                      title={`Copy ${z} ${hex} (click)`}
                      aria-label={`Copy ${z} color ${hex} to clipboard`}
                      onClick={() => void copySwatchColor(hex, z)}
                      style={{
                        width: 18,
                        height: 18,
                        borderRadius: 2,
                        background: hex,
                        border: "1px solid #555",
                        flexShrink: 0,
                        cursor: "pointer",
                        padding: 0,
                      }}
                    />
                  );
                })}
              </div>
              <button type="button" style={btnPrimary} onClick={() => applyElement(id)}>
                Apply
              </button>
              {suggested === id ? (
                <span style={{ fontSize: 10, color: "#6b9e7a", marginLeft: 4 }}>suggested</span>
              ) : null}
            </div>
          );
        })
      )}
    </div>
  );
}
