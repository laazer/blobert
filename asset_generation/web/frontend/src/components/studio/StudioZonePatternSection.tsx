import { useMemo } from "react";
import type { BuildControlDef } from "../../types";
import type { CoarseZoneKey } from "../../utils/elementColorPalettes";
import {
  buildStudioPatternTiles,
  patternTileHuePreviewStyle,
  textureModeFromTileId,
  tileIdFromTextureMode,
} from "../../utils/studioPatternPreview";
import { textureModeOptionsForZone } from "../../utils/studioElementDefaultKeys";
import { normalizedTextureMode } from "../Preview/ZoneTextureBlock";
import { STUDIO_SURFACE_PANEL } from "../../styles/studioTokens";
import { StudioPanelHead } from "./StudioPanelHead";
import { StudioZoneFill, type StudioZoneFillBindings } from "./StudioZoneFill";

type Props = {
  slug: string;
  zone: CoarseZoneKey;
  defs: readonly BuildControlDef[];
  knownDefKeys: ReadonlySet<string>;
  values: Readonly<Record<string, unknown>>;
  accentHue: string;
  accentInk: string;
  paletteColors?: readonly string[];
  bindings: StudioZoneFillBindings;
  onSetTextureMode: (mode: string) => void;
};

export function StudioZonePatternSection({
  slug,
  zone,
  defs,
  knownDefKeys,
  values,
  accentHue,
  accentInk,
  paletteColors,
  bindings,
  onSetTextureMode,
}: Props) {
  const textureModeOptions = useMemo(
    () => textureModeOptionsForZone(zone, defs),
    [zone, defs],
  );
  const patternTiles = useMemo(
    () => buildStudioPatternTiles(textureModeOptions),
    [textureModeOptions],
  );
  if (patternTiles.length === 0) return null;

  const textureMode = normalizedTextureMode(zone, values);
  const activePatternTileId = tileIdFromTextureMode(textureMode, patternTiles);
  const patternPlain = textureMode === "none";

  return (
    <div data-testid={`studio-zone-pattern-${zone}`}>
      <StudioPanelHead title="Pattern" subtitle="Overlay shape, then its fill" />
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
              data-testid={`studio-look-pattern-${zone}-${tile.id}`}
              aria-pressed={active}
              onClick={() => onSetTextureMode(textureModeFromTileId(tile.id, patternTiles))}
              style={{
                padding: 0,
                borderRadius: 7,
                background: STUDIO_SURFACE_PANEL,
                border: active ? `1px solid ${accentHue}` : "1px solid rgba(255,255,255,0.06)",
                cursor: "pointer",
                overflow: "hidden",
                height: 56,
                display: "flex",
                flexDirection: "column",
              }}
            >
              <div style={patternTileHuePreviewStyle(tile.textureMode, accentHue)} />
              <div
                style={{
                  padding: "3px 0",
                  fontSize: 9,
                  color: active ? accentInk : "#8a8a96",
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
        <div data-testid={`studio-zone-pattern-fill-${zone}`}>
          <StudioPanelHead title="Pattern fill" subtitle="What the pattern is drawn with" />
          <StudioZoneFill
            slug={slug}
            zone={zone}
            fillRole="pattern"
            accentHue={accentHue}
            paletteColors={paletteColors}
            embedded
            bindings={bindings}
            knownDefKeys={knownDefKeys}
          />
        </div>
      ) : null}
    </div>
  );
}
