import { useAppStore } from "../../store/useAppStore";
import type { AnimatedBuildControlDef } from "../../types";
import { SingleColorMode } from "../ColorPicker/modes/SingleColorMode";
import { ControlRow, rowStyles } from "./BuildControlRow";
import { zonePartDisplayName } from "./ZoneTextureBlock";
import {
  isExtraZoneAppearanceDefKey,
  partitionZoneExtraDefs,
} from "./zoneExtrasPartition";

const EMPTY_DEFS: readonly AnimatedBuildControlDef[] = [];
const EMPTY_VALUES: Readonly<Record<string, unknown>> = {};

type Props = {
  slug: string;
};

function hexFromStore(raw: unknown): string {
  if (typeof raw !== "string") return "";
  return raw.trim().replace(/^#/, "").toLowerCase().slice(0, 6);
}

/**
 * Per-zone finish + hex for geometry extras (``extra_zone_*``). Shown on Colors only (single color, no patterns).
 */
export function ExtraZoneMaterialControls({ slug }: Props) {
  const defs = useAppStore((st) => st.animatedBuildControls[slug] ?? EMPTY_DEFS);
  const values = useAppStore((st) => st.animatedBuildOptionValues[slug] ?? EMPTY_VALUES);
  const setAnimatedBuildOption = useAppStore((st) => st.setAnimatedBuildOption);

  const extraDefs = defs.filter((d) => d.key.startsWith("extra_zone_"));
  const { zones, byZone, hasAny } = partitionZoneExtraDefs(slug, extraDefs);
  if (!hasAny) return null;

  const zonesWithColor = zones.filter((zone) => {
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
        const hexKey = `extra_zone_${zone}_hex`;
        const title = zonePartDisplayName(zone);

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
            <SingleColorMode
              color={hexFromStore(values[hexKey])}
              onChange={(h) => setAnimatedBuildOption(slug, hexKey, h)}
            />
          </div>
        );
      })}
    </div>
  );
}
