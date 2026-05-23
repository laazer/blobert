import { useMemo } from "react";
import { useAppStore } from "../../store/useAppStore";
import type { AnimatedBuildControlDef } from "../../types";
import { SingleColorMode } from "../ColorPicker/modes/SingleColorMode";
import { StudioPartMaterialFill } from "../studio/StudioPartMaterialFill";
import { ControlRow, rowStyles } from "./BuildControlRow";
import { zonePartDisplayName } from "./ZoneTextureBlock";
import {
  isExtraZoneAppearanceDefKey,
  partitionZoneExtraDefs,
} from "./zoneExtrasPartition";

const EMPTY_DEFS: readonly AnimatedBuildControlDef[] = [];
const EMPTY_VALUES: Readonly<Record<string, unknown>> = {};

function hexFromStore(raw: unknown): string {
  if (typeof raw !== "string") return "";
  return raw.trim().replace(/^#/, "").toLowerCase().slice(0, 6);
}

type Props = {
  slug: string;
  /** Studio Look: only show extras for this coarse zone */
  zoneFilter?: string;
  /** Use studio material fill picker instead of legacy single-color mode */
  useStudioPicker?: boolean;
  accentHue?: string;
  paletteColors?: readonly string[];
};

/**
 * Per-zone finish + material fill for geometry extras (``extra_zone_*``). Shown on Colors / Studio advanced.
 */
export function ExtraZoneMaterialControls({
  slug,
  zoneFilter,
  useStudioPicker = false,
  accentHue = "210",
  paletteColors,
}: Props) {
  const defs = useAppStore((st) => st.animatedBuildControls[slug] ?? EMPTY_DEFS);
  const values = useAppStore((st) => st.animatedBuildOptionValues[slug] ?? EMPTY_VALUES);
  const setAnimatedBuildOption = useAppStore((st) => st.setAnimatedBuildOption);

  const knownDefKeys = useMemo(() => new Set(defs.map((d) => d.key)), [defs]);

  const extraDefs = defs.filter((d) => d.key.startsWith("extra_zone_"));
  const { zones, byZone, hasAny } = partitionZoneExtraDefs(slug, extraDefs);
  if (!hasAny) return null;

  const zonesWithColor = zones.filter((zone) => {
    if (zoneFilter && zone !== zoneFilter) return false;
    const zdefs = byZone[zone] ?? [];
    return zdefs.some((d) => isExtraZoneAppearanceDefKey(d.key));
  });
  if (zonesWithColor.length === 0) return null;

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        gap: 8,
        marginTop: 10,
        paddingTop: 10,
        borderTop: "1px solid #3c3c3c",
      }}
    >
      <span style={{ ...rowStyles.label, fontWeight: 600 }}>Geometry extra materials (per zone)</span>
      <p style={{ color: "#8f8f8f", fontSize: 11, margin: 0, lineHeight: 1.4 }}>
        Tint for spikes, bulbs, horns, and shell geometry. Kind and placement stay on the{" "}
        <strong style={{ color: "#bbb" }}>Extras</strong> tab.
      </p>
      {zonesWithColor.map((zone) => {
        const zdefs = byZone[zone] ?? [];
        const finishDef = zdefs.find((d) => d.key === `extra_zone_${zone}_finish`);
        const materialPrefix = `extra_zone_${zone}_material`;
        const legacyHexKey = `extra_zone_${zone}_hex`;
        const title = zonePartDisplayName(zone);
        const hasMaterialFill = knownDefKeys.has(materialPrefix);

        return (
          <div
            key={zone}
            style={{
              display: "flex",
              flexDirection: "column",
              gap: 8,
              paddingBottom: 8,
              borderBottom: "1px solid #2d2d2d",
            }}
          >
            <span style={{ color: "#858585", fontSize: 11, fontWeight: 600 }}>
              Extra geometry — {title}
            </span>
            {finishDef ? (
              <ControlRow
                def={finishDef}
                value={values[finishDef.key]}
                onChange={(v) => setAnimatedBuildOption(slug, finishDef.key, v)}
              />
            ) : null}
            {hasMaterialFill ? (
              <StudioPartMaterialFill
                slug={slug}
                materialPrefix={materialPrefix}
                legacyHexKey={legacyHexKey}
                accentHue={accentHue}
                paletteColors={useStudioPicker ? paletteColors : undefined}
                testId={`studio-extra-material-${zone}`}
              />
            ) : (
              <SingleColorMode
                color={hexFromStore(values[legacyHexKey])}
                onChange={(h) => setAnimatedBuildOption(slug, legacyHexKey, h)}
              />
            )}
          </div>
        );
      })}
    </div>
  );
}
