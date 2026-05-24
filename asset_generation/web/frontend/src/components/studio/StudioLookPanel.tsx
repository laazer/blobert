import { useCallback, useMemo, useState, type CSSProperties } from "react";
import { ELEMENTS, type ElementId } from "../../constants/elements";
import { STUDIO_INK_MUTED, STUDIO_SURFACE_PANEL } from "../../styles/studioTokens";
import { useAppStore } from "../../store/useAppStore";
import {
  ELEMENT_IDS,
  defaultElementForSlug,
  sanitizeFinish,
  sanitizeHex,
  type CoarseZoneKey,
  type ElementId as PaletteElementId,
} from "../../utils/elementColorPalettes";
import { buildElementApplyUpdates } from "../../utils/elementPaletteOverrides";
import { useElementPaletteCatalog } from "../../hooks/useElementPaletteCatalog";
import { inferFamilyElementId } from "../../utils/inferFamilyElement";
import {
  buildStudioPatternTiles,
  patternTileHuePreviewStyle,
  textureModeFromTileId,
  tileIdFromTextureMode,
} from "../../utils/studioPatternPreview";
import {
  coarseZonesWithMaterial,
  paletteSwatchColors,
  zoneToPartLabel,
} from "../../utils/studioLookMaterial";
import { normalizedTextureMode } from "../Preview/ZoneTextureBlock";
import { ZONE_FINISH_HEX_RE } from "../Preview/featureMaterialPartition";
import { StudioPanelHead } from "./StudioPanelHead";
import { StudioPartContextBar } from "./StudioPartContextBar";
import { StudioPartPicker } from "./StudioPartPicker";
import { ElementPaletteDefaultsModal } from "./ElementPaletteDefaultsModal";
import { StudioZoneFill } from "./StudioZoneFill";

type Props = {
  slug: string;
  activeZone?: CoarseZoneKey;
  onActiveZoneChange?: (zone: CoarseZoneKey) => void;
};

const sectionGap: CSSProperties = { display: "flex", flexDirection: "column", gap: 18 };

export function StudioLookPanel({ slug, activeZone: activeZoneProp, onActiveZoneChange }: Props) {
  const defs = useAppStore((s) => s.animatedBuildControls[slug] ?? []);
  const values = useAppStore((s) => s.animatedBuildOptionValues[slug] ?? {});
  const applyBulk = useAppStore((s) => s.applyAnimatedBuildOptionsForSlug);
  const setOption = useAppStore((s) => s.setAnimatedBuildOption);
  const setCommandExport = useAppStore((s) => s.setCommandExport);
  const commandEnemy = useAppStore((s) => s.commandContext.enemy);

  const [pickedElement, setPickedElement] = useState<ElementId | null>(null);
  const [configElementId, setConfigElementId] = useState<ElementId | null>(null);
  const [internalActiveZone, setInternalActiveZone] = useState<CoarseZoneKey>("body");
  const { getPalette, isOverridden, saveMaterialDefaults, resetPalette } = useElementPaletteCatalog();
  const activeZone = activeZoneProp ?? internalActiveZone;
  const setActiveZone = onActiveZoneChange ?? setInternalActiveZone;

  const knownDefKeys = useMemo(() => new Set(defs.map((d) => d.key)), [defs]);
  const hasCoarseZones = defs.some((d) => ZONE_FINISH_HEX_RE.test(d.key));
  const partZones = useMemo(() => coarseZonesWithMaterial(knownDefKeys), [knownDefKeys]);

  const displayElementId: ElementId = useMemo(() => {
    if (pickedElement) return pickedElement;
    const suggested = defaultElementForSlug(slug);
    if (suggested) return suggested as ElementId;
    const family = commandEnemy.trim();
    if (family) return inferFamilyElementId(family, []);
    return "physical";
  }, [pickedElement, slug, commandEnemy]);

  const elToken = ELEMENTS[displayElementId];
  const palette = getPalette(displayElementId as PaletteElementId);
  const paletteColors = useMemo(() => paletteSwatchColors(palette), [palette]);

  const effectiveZone = partZones.includes(activeZone) ? activeZone : (partZones[0] ?? "body");
  const activePartLabel = zoneToPartLabel(effectiveZone);

  const textureMode = normalizedTextureMode(effectiveZone, values);

  const textureModeDef = defs.find((d) => d.key === `feat_${effectiveZone}_texture_mode`);
  const textureModeOptions = useMemo(() => {
    if (textureModeDef?.type === "select_str" && textureModeDef.options.length > 0) {
      return textureModeDef.options.map((o) => o.toLowerCase());
    }
    return ["none", "spots", "stripes", "checkerboard"];
  }, [textureModeDef]);

  const patternTiles = useMemo(
    () => buildStudioPatternTiles(textureModeOptions),
    [textureModeOptions],
  );
  const activePatternTileId = tileIdFromTextureMode(textureMode, patternTiles);
  const patternPlain = textureMode === "none";

  const applyElement = useCallback(
    (id: ElementId) => {
      setPickedElement(id);
      const pal = getPalette(id as PaletteElementId);
      const updates = buildElementApplyUpdates(id as PaletteElementId, knownDefKeys, values);
      if (Object.keys(updates).length > 0) applyBulk(slug, updates);
      const body = pal.body;
      if (body) {
        const hex = sanitizeHex(body.hex);
        setCommandExport({
          finish: sanitizeFinish(body.finish),
          hexColor: hex,
        });
      }
    },
    [slug, knownDefKeys, values, applyBulk, setCommandExport, getPalette],
  );

  const setZoneFinish = useCallback(
    (zone: CoarseZoneKey, finish: string) => {
      const key = `feat_${zone}_finish`;
      if (knownDefKeys.has(key)) setOption(slug, key, finish);
    },
    [slug, knownDefKeys, setOption],
  );

  const setPatternMode = useCallback(
    (tileId: string) => {
      const key = `feat_${effectiveZone}_texture_mode`;
      if (knownDefKeys.has(key)) {
        setOption(slug, key, textureModeFromTileId(tileId, patternTiles));
      }
    },
    [slug, effectiveZone, knownDefKeys, setOption, patternTiles],
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
        <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 6 }}>
          {ELEMENT_IDS.map((id) => {
            const e = ELEMENTS[id as ElementId];
            const active = displayElementId === id;
            const customized = isOverridden(id as PaletteElementId);
            return (
              <div
                key={id}
                style={{
                  display: "flex",
                  alignItems: "stretch",
                  gap: 0,
                  borderRadius: 7,
                  overflow: "hidden",
                  border: active ? `1px solid ${e.hue}` : "1px solid rgba(255,255,255,0.06)",
                  background: active ? e.soft : STUDIO_SURFACE_PANEL,
                }}
              >
                <button
                  type="button"
                  data-testid={`studio-look-element-${id}`}
                  aria-pressed={active}
                  onClick={() => applyElement(id as ElementId)}
                  style={{
                    display: "flex",
                    alignItems: "center",
                    gap: 6,
                    padding: "8px 6px 8px 8px",
                    border: 0,
                    background: "transparent",
                    cursor: "pointer",
                    textAlign: "left",
                    flex: 1,
                    minWidth: 0,
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
                      overflow: "hidden",
                      textOverflow: "ellipsis",
                      whiteSpace: "nowrap",
                    }}
                  >
                    {e.name}
                    {customized ? (
                      <span
                        style={{
                          marginLeft: 4,
                          fontSize: 9,
                          color: active ? e.ink : "#7a7a86",
                          fontWeight: 700,
                        }}
                        aria-hidden
                      >
                        •
                      </span>
                    ) : null}
                  </span>
                </button>
                <button
                  type="button"
                  data-testid={`studio-look-element-config-${id}`}
                  aria-label={`Configure ${e.name} element defaults`}
                  title={`Configure ${e.name} defaults`}
                  onClick={() => setConfigElementId(id as ElementId)}
                  style={{
                    width: 28,
                    flexShrink: 0,
                    border: 0,
                    borderLeft: "1px solid rgba(255,255,255,0.06)",
                    background: active ? "rgba(0,0,0,0.12)" : "rgba(255,255,255,0.03)",
                    color: active ? e.ink : "#8a8a96",
                    cursor: "pointer",
                    fontSize: 13,
                    lineHeight: 1,
                    padding: 0,
                  }}
                >
                  ⚙
                </button>
              </div>
            );
          })}
        </div>
        {configElementId ? (
          <ElementPaletteDefaultsModal
            open
            slug={slug}
            elementId={configElementId}
            defs={defs}
            knownDefKeys={knownDefKeys}
            onClose={() => setConfigElementId(null)}
            onSave={(draft) => saveMaterialDefaults(configElementId, draft, knownDefKeys)}
            onResetBuiltin={() => resetPalette(configElementId)}
          />
        ) : null}
      </section>

      <section data-testid="studio-look-parts">
        <StudioPanelHead
          title="Parts"
          subtitle="Pick a part to edit. Each part has its own background, pattern, and finish."
        />
        <StudioPartPicker
          zones={partZones}
          activeZone={effectiveZone}
          elementHue={elToken.hue}
          values={values}
          onSelectZone={setActiveZone}
        />
        <StudioPartContextBar
          zone={effectiveZone}
          values={values}
          knownDefKeys={knownDefKeys}
          onFinishChange={(f) => setZoneFinish(effectiveZone, f)}
        />
      </section>

      <section data-testid="studio-look-background">
        <StudioPanelHead
          title={`Background · ${activePartLabel}`}
          subtitle="Base layer for this part"
        />
        <StudioZoneFill
          slug={slug}
          zone={effectiveZone}
          fillRole="background"
          accentHue={elToken.hue}
          paletteColors={paletteColors}
        />
      </section>

      {patternTiles.length > 0 ? (
        <section data-testid="studio-look-pattern">
          <StudioPanelHead
            title={`Pattern · ${activePartLabel}`}
            subtitle="Overlay shape, then its fill"
          />
          <div
            style={{
              display: "grid",
              gridTemplateColumns: `repeat(${Math.min(patternTiles.length, 5)}, 1fr)`,
              gap: 6,
              marginBottom: 12,
            }}
          >
            {patternTiles.map((tile) => {
              const active = activePatternTileId === tile.id;
              return (
                <button
                  key={tile.id}
                  type="button"
                  data-testid={`studio-look-pattern-${effectiveZone}-${tile.id}`}
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
                  <div style={patternTileHuePreviewStyle(tile.textureMode, elToken.hue)} />
                  <div
                    style={{
                      padding: "3px 0",
                      fontSize: 9,
                      color: active ? elToken.ink : "#8a8a96",
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

          {!patternPlain ? (
            <div data-testid="studio-look-pattern-fill">
              <StudioPanelHead title="Pattern fill" subtitle="What the pattern is drawn with" />
              <StudioZoneFill
                slug={slug}
                zone={effectiveZone}
                fillRole="pattern"
                accentHue={elToken.hue}
                paletteColors={paletteColors}
                embedded
              />
            </div>
          ) : null}
        </section>
      ) : null}
    </div>
  );
}
