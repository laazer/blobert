import { useCallback, useMemo, useState, type CSSProperties } from "react";
import { ELEMENTS, type ElementId } from "../../constants/elements";
import { STUDIO_INK_MUTED, STUDIO_INK_PRIMARY, STUDIO_SURFACE_PANEL } from "../../styles/studioTokens";
import { useAppStore } from "../../store/useAppStore";
import {
  DEFAULT_ELEMENT_PALETTES,
  ELEMENT_IDS,
  buildFeatUpdatesFromPalette,
  defaultElementForSlug,
  type ElementId as PaletteElementId,
} from "../../utils/elementColorPalettes";
import { inferFamilyElementId } from "../../utils/inferFamilyElement";
import {
  STUDIO_PATTERN_TILES,
  patternTilePreviewStyle,
  type PatternTileId,
} from "../../utils/studioPatternPreview";
import {
  STUDIO_BODY_FINISH_PILLS,
  STUDIO_PATTERN_COLOR_SWATCHES,
  buildZoneHexUpdates,
  coarseZonesWithMaterial,
  finishPillSelected,
  paletteSwatchColors,
  partRowLabel,
  readZoneFinish,
  readZoneHex,
} from "../../utils/studioLookMaterial";
import { normalizedTextureMode } from "../Preview/ZoneTextureBlock";
import { ZONE_FINISH_HEX_RE } from "../Preview/featureMaterialPartition";
import { StudioPanelHead } from "./StudioPanelHead";
import { StudioSwatch } from "./StudioSwatch";

type Props = { slug: string };

const sectionGap: CSSProperties = { display: "flex", flexDirection: "column", gap: 18 };

const labelCaps: CSSProperties = {
  fontSize: 10,
  color: STUDIO_INK_MUTED,
  fontWeight: 600,
  letterSpacing: 0.6,
  textTransform: "uppercase",
  marginBottom: 6,
};

function textureModeToTileId(mode: string): PatternTileId {
  const tile = STUDIO_PATTERN_TILES.find((t) => t.textureMode === mode);
  return tile?.id ?? "plain";
}

function tileIdToTextureMode(tileId: PatternTileId): string {
  return STUDIO_PATTERN_TILES.find((t) => t.id === tileId)?.textureMode ?? "none";
}

export function StudioLookPanel({ slug }: Props) {
  const defs = useAppStore((s) => s.animatedBuildControls[slug] ?? []);
  const values = useAppStore((s) => s.animatedBuildOptionValues[slug] ?? {});
  const applyBulk = useAppStore((s) => s.applyAnimatedBuildOptionsForSlug);
  const setOption = useAppStore((s) => s.setAnimatedBuildOption);
  const commandEnemy = useAppStore((s) => s.commandContext.enemy);

  const [pickedElement, setPickedElement] = useState<ElementId | null>(null);

  const knownDefKeys = useMemo(() => new Set(defs.map((d) => d.key)), [defs]);

  const hasCoarseZones = defs.some((d) => ZONE_FINISH_HEX_RE.test(d.key));

  const displayElementId: ElementId = useMemo(() => {
    if (pickedElement) return pickedElement;
    const suggested = defaultElementForSlug(slug);
    if (suggested) return suggested as ElementId;
    const family = commandEnemy.trim();
    if (family) return inferFamilyElementId(family, []);
    return "physical";
  }, [pickedElement, slug, commandEnemy]);

  const elToken = ELEMENTS[displayElementId];
  const palette = DEFAULT_ELEMENT_PALETTES[displayElementId as PaletteElementId];
  const paletteColors = useMemo(() => paletteSwatchColors(palette), [palette]);

  const bodyHex = readZoneHex(values, "body") || palette.body?.hex || "#888888";
  const bodyFinish = readZoneFinish(values, "body");
  const textureMode = normalizedTextureMode("body", values);
  const activePatternTile = textureModeToTileId(textureMode);

  const patternHexKey = "feat_body_texture_pattern_hex";
  const patternHexRaw = values[patternHexKey];
  const patternHex =
    typeof patternHexRaw === "string" && patternHexRaw.trim() !== ""
      ? patternHexRaw.trim()
      : STUDIO_PATTERN_COLOR_SWATCHES[0];

  const textureModeDef = defs.find((d) => d.key === "feat_body_texture_mode");
  const textureModeOptions = useMemo(() => {
    if (textureModeDef?.type === "select_str" && textureModeDef.options.length > 0) {
      return textureModeDef.options.map((o) => o.toLowerCase());
    }
    return ["none", "spots", "stripes", "checkerboard", "assets"];
  }, [textureModeDef]);

  const visiblePatternTiles = useMemo(
    () =>
      STUDIO_PATTERN_TILES.filter((t) => textureModeOptions.includes(t.textureMode)),
    [textureModeOptions],
  );

  const partZones = useMemo(() => coarseZonesWithMaterial(knownDefKeys), [knownDefKeys]);

  const applyElement = useCallback(
    (id: ElementId) => {
      setPickedElement(id);
      const pal = DEFAULT_ELEMENT_PALETTES[id as PaletteElementId];
      const updates = buildFeatUpdatesFromPalette(pal, knownDefKeys, values);
      if (Object.keys(updates).length > 0) applyBulk(slug, updates);
    },
    [slug, knownDefKeys, values, applyBulk],
  );

  const setBodyHex = useCallback(
    (hex: string) => {
      const updates = buildZoneHexUpdates("body", hex, knownDefKeys);
      if (Object.keys(updates).length > 0) applyBulk(slug, updates);
    },
    [slug, knownDefKeys, applyBulk],
  );

  const setBodyFinish = useCallback(
    (finish: string) => {
      if (knownDefKeys.has("feat_body_finish")) {
        setOption(slug, "feat_body_finish", finish);
      }
    },
    [slug, knownDefKeys, setOption],
  );

  const setPatternMode = useCallback(
    (tileId: PatternTileId) => {
      if (!knownDefKeys.has("feat_body_texture_mode")) return;
      setOption(slug, "feat_body_texture_mode", tileIdToTextureMode(tileId));
    },
    [slug, knownDefKeys, setOption],
  );

  const setPatternColor = useCallback(
    (hex: string) => {
      if (knownDefKeys.has(patternHexKey)) {
        setOption(slug, patternHexKey, hex);
      }
    },
    [slug, knownDefKeys, setOption],
  );

  if (!hasCoarseZones) {
    return (
      <p data-testid="studio-look-no-zones" style={{ color: STUDIO_INK_MUTED, fontSize: 11, margin: 0 }}>
        No coarse zone controls loaded for this asset yet.
      </p>
    );
  }

  return (
    <div data-testid="studio-look-panel" style={sectionGap}>
      <section data-testid="studio-look-element-grid">
        <StudioPanelHead title="Element" subtitle="Drives palette + animation hints" />
        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(3, 1fr)",
            gap: 6,
          }}
        >
          {ELEMENT_IDS.map((id) => {
            const e = ELEMENTS[id as ElementId];
            const active = displayElementId === id;
            return (
              <button
                key={id}
                type="button"
                data-testid={`studio-look-element-${id}`}
                aria-pressed={active}
                onClick={() => applyElement(id as ElementId)}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 6,
                  padding: "8px 8px",
                  borderRadius: 7,
                  background: active ? e.soft : STUDIO_SURFACE_PANEL,
                  border: active ? `1px solid ${e.hue}` : "1px solid rgba(255,255,255,0.06)",
                  cursor: "pointer",
                  textAlign: "left",
                }}
              >
                <span
                  style={{
                    width: 10,
                    height: 10,
                    borderRadius: "50%",
                    background: e.hue,
                    boxShadow: `0 0 6px ${e.hue}80`,
                    flexShrink: 0,
                  }}
                />
                <span
                  style={{
                    fontSize: 11,
                    fontWeight: 600,
                    color: active ? e.ink : "#bababf",
                  }}
                >
                  {e.name}
                </span>
              </button>
            );
          })}
        </div>
      </section>

      <section data-testid="studio-look-body">
        <StudioPanelHead
          title="Body"
          subtitle="Base color · finish · pattern"
          right={
            <span style={{ fontSize: 10, color: "#5a5a66", fontFamily: "var(--font-mono, monospace)" }}>
              {partZones.length} parts
            </span>
          }
        />
        <div
          style={{
            background: "#0a0a10",
            borderRadius: 10,
            padding: 12,
            display: "flex",
            flexDirection: "column",
            gap: 12,
            border: "1px solid rgba(255,255,255,0.04)",
          }}
        >
          <div>
            <div style={labelCaps}>
              Palette · {elToken.name}
            </div>
            <div style={{ display: "flex", gap: 6, alignItems: "center", flexWrap: "wrap" }}>
              {paletteColors.map((c) => (
                <StudioSwatch
                  key={c}
                  color={c}
                  size={26}
                  selected={bodyHex.toLowerCase() === c.toLowerCase()}
                  onClick={() => setBodyHex(c)}
                  data-testid={`studio-look-body-swatch-${c}`}
                />
              ))}
            </div>
          </div>
          <div style={{ display: "flex", gap: 10, alignItems: "flex-start" }}>
            <div style={{ flex: 1 }}>
              <div style={labelCaps}>Hex</div>
              <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
                <label
                  style={{
                    width: 22,
                    height: 22,
                    borderRadius: 5,
                    background: bodyHex,
                    boxShadow: "0 0 0 1px rgba(255,255,255,0.1)",
                    overflow: "hidden",
                    cursor: "pointer",
                    flexShrink: 0,
                  }}
                >
                  <input
                    type="color"
                    value={bodyHex.startsWith("#") ? bodyHex : "#888888"}
                    aria-label="Body hex color"
                    data-testid="studio-look-body-hex-input"
                    style={{ opacity: 0, width: "100%", height: "100%", cursor: "pointer", border: 0 }}
                    onChange={(e) => setBodyHex(e.target.value)}
                  />
                </label>
                <span
                  style={{
                    fontFamily: "var(--font-mono, monospace)",
                    fontSize: 12,
                    color: STUDIO_INK_PRIMARY,
                  }}
                >
                  {bodyHex}
                </span>
              </div>
            </div>
            <div style={{ flex: 1 }}>
              <div style={labelCaps}>Finish</div>
              <div style={{ display: "flex", gap: 4 }}>
                {STUDIO_BODY_FINISH_PILLS.map((f) => {
                  const active = finishPillSelected(bodyFinish, f);
                  return (
                    <button
                      key={f}
                      type="button"
                      data-testid={`studio-look-body-finish-${f}`}
                      aria-pressed={active}
                      onClick={() => setBodyFinish(f)}
                      style={{
                        flex: 1,
                        padding: "5px 4px",
                        borderRadius: 5,
                        background: active ? "#23232e" : "transparent",
                        border: "1px solid rgba(255,255,255,0.06)",
                        color: active ? STUDIO_INK_PRIMARY : "#8a8a96",
                        fontSize: 10,
                        fontWeight: 600,
                        cursor: "pointer",
                      }}
                    >
                      {f}
                    </button>
                  );
                })}
              </div>
            </div>
          </div>
        </div>
      </section>

      {visiblePatternTiles.length > 0 ? (
        <section data-testid="studio-look-pattern">
          <StudioPanelHead title="Pattern" subtitle="Overlay on body" />
          <div
            style={{
              display: "grid",
              gridTemplateColumns: `repeat(${Math.min(visiblePatternTiles.length, 5)}, 1fr)`,
              gap: 6,
            }}
          >
            {visiblePatternTiles.map((tile) => {
              const active = activePatternTile === tile.id;
              return (
                <button
                  key={tile.id}
                  type="button"
                  data-testid={`studio-look-pattern-${tile.id}`}
                  aria-pressed={active}
                  onClick={() => setPatternMode(tile.id)}
                  style={{
                    padding: 0,
                    borderRadius: 7,
                    background: STUDIO_SURFACE_PANEL,
                    border: active ? `1px solid ${elToken.hue}` : "1px solid rgba(255,255,255,0.06)",
                    cursor: "pointer",
                    overflow: "hidden",
                    height: 56,
                    display: "flex",
                    flexDirection: "column",
                  }}
                >
                  <div style={patternTilePreviewStyle(tile.id, bodyHex, patternHex)} />
                  <div
                    style={{
                      padding: "3px 0",
                      fontSize: 9,
                      color: "#8a8a96",
                      textAlign: "center",
                      fontWeight: 600,
                      textTransform: "uppercase",
                      letterSpacing: 0.5,
                    }}
                  >
                    {tile.label}
                  </div>
                </button>
              );
            })}
          </div>
          {knownDefKeys.has(patternHexKey) ? (
            <div style={{ marginTop: 10 }}>
              <div style={labelCaps}>Pattern color</div>
              <div style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
                {STUDIO_PATTERN_COLOR_SWATCHES.map((c) => (
                  <StudioSwatch
                    key={c}
                    color={c}
                    size={22}
                    selected={patternHex.toLowerCase() === c.toLowerCase()}
                    onClick={() => setPatternColor(c)}
                    data-testid={`studio-look-pattern-color-${c}`}
                  />
                ))}
              </div>
            </div>
          ) : null}
        </section>
      ) : null}

      <section data-testid="studio-look-parts">
        <StudioPanelHead title="Parts" subtitle="Override per zone" />
        <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
          {partZones.map((zone) => {
            const hex = readZoneHex(values, zone) || "—";
            const finish = readZoneFinish(values, zone);
            return (
              <div
                key={zone}
                data-testid={`studio-look-part-${zone}`}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 10,
                  padding: "8px 10px",
                  borderRadius: 7,
                  background: STUDIO_SURFACE_PANEL,
                  border: "1px solid rgba(255,255,255,0.04)",
                }}
              >
                <div
                  style={{
                    width: 18,
                    height: 18,
                    borderRadius: 4,
                    background: hex.startsWith("#") ? hex : "#333",
                    boxShadow: "0 0 0 1px rgba(255,255,255,0.08)",
                    flexShrink: 0,
                  }}
                />
                <div style={{ fontSize: 12, fontWeight: 600, color: STUDIO_INK_PRIMARY, flex: 1 }}>
                  {partRowLabel(zone)}
                </div>
                <div
                  style={{
                    fontSize: 10,
                    color: STUDIO_INK_MUTED,
                    fontFamily: "var(--font-mono, monospace)",
                  }}
                >
                  {hex}
                </div>
                <div
                  style={{
                    fontSize: 10,
                    color: STUDIO_INK_MUTED,
                    fontFamily: "var(--font-mono, monospace)",
                    minWidth: 50,
                    textAlign: "right",
                  }}
                >
                  {finish}
                </div>
              </div>
            );
          })}
        </div>
      </section>
    </div>
  );
}
