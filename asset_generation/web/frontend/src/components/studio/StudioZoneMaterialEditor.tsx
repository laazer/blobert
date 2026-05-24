import { useCallback } from "react";
import type { BuildControlDef } from "../../types";
import type { CoarseZoneKey } from "../../utils/elementColorPalettes";
import { zoneToPartLabel } from "../../utils/studioLookMaterial";
import { STUDIO_INK_SECONDARY, STUDIO_SURFACE_PANEL } from "../../styles/studioTokens";
import { StudioPanelHead } from "./StudioPanelHead";
import { StudioPartContextBar } from "./StudioPartContextBar";
import { StudioZoneFill, type StudioZoneFillBindings } from "./StudioZoneFill";
import { StudioZonePatternSection } from "./StudioZonePatternSection";

type Props = {
  slug: string;
  zone: CoarseZoneKey;
  defs: readonly BuildControlDef[];
  knownDefKeys: ReadonlySet<string>;
  bindings: StudioZoneFillBindings;
  accentHue: string;
  accentInk: string;
  paletteColors?: readonly string[];
};

export function StudioZoneMaterialEditor({
  slug,
  zone,
  defs,
  knownDefKeys,
  bindings,
  accentHue,
  accentInk,
  paletteColors,
}: Props) {
  const label = zoneToPartLabel(zone);
  const values = bindings.values;

  const onFinishChange = useCallback(
    (finish: string) => {
      const key = `feat_${zone}_finish`;
      if (knownDefKeys.has(key)) bindings.setOption(key, finish);
    },
    [zone, knownDefKeys, bindings],
  );

  const onSetTextureMode = useCallback(
    (mode: string) => {
      const key = `feat_${zone}_texture_mode`;
      if (knownDefKeys.has(key)) bindings.setOption(key, mode);
    },
    [zone, knownDefKeys, bindings],
  );

  return (
    <section
      data-testid={`element-defaults-zone-${zone}`}
      style={{
        padding: "10px 12px",
        borderRadius: 8,
        background: STUDIO_SURFACE_PANEL,
        border: "1px solid rgba(255,255,255,0.04)",
        display: "flex",
        flexDirection: "column",
        gap: 12,
      }}
    >
      <div style={{ fontSize: 13, fontWeight: 700, color: STUDIO_INK_SECONDARY }}>{label}</div>

      <StudioPartContextBar
        zone={zone}
        values={values}
        knownDefKeys={knownDefKeys}
        onFinishChange={onFinishChange}
      />

      <div>
        <StudioPanelHead title="Background" subtitle="Base layer for this part" />
        <StudioZoneFill
          slug={slug}
          zone={zone}
          fillRole="background"
          accentHue={accentHue}
          paletteColors={paletteColors}
          bindings={bindings}
          knownDefKeys={knownDefKeys}
        />
      </div>

      <StudioZonePatternSection
        slug={slug}
        zone={zone}
        defs={defs}
        knownDefKeys={knownDefKeys}
        values={values}
        accentHue={accentHue}
        accentInk={accentInk}
        paletteColors={paletteColors}
        bindings={bindings}
        onSetTextureMode={onSetTextureMode}
      />
    </section>
  );
}
