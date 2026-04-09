import { useAppStore } from "../../store/useAppStore";
import type { AnimatedBuildControlDef } from "../../types";
import { ControlRow, rowStyles } from "./BuildControlRow";
import {
  kindOptionsForZone,
  partitionZoneExtraDefs,
} from "./zoneExtrasPartition";

const EMPTY_DEFS: readonly AnimatedBuildControlDef[] = [];
const EMPTY_VALUES: Readonly<Record<string, unknown>> = {};

const titleStyle = rowStyles.label;

type Props = {
  slug: string;
  showEmptyHint?: boolean;
};

function effectiveKind(zone: string, raw: string): string {
  if (zone === "head") return raw;
  return raw === "horns" ? "none" : raw;
}

function rowDisabled(kind: string, defKey: string): boolean {
  if (defKey.endsWith("_kind") || defKey.endsWith("_finish") || defKey.endsWith("_hex")) {
    return false;
  }
  if (kind === "none" || kind === "shell") {
    return defKey.includes("_spike_") || defKey.includes("_bulb_");
  }
  if (kind === "spikes") {
    return defKey.includes("_bulb_");
  }
  if (kind === "horns") {
    return defKey.includes("_spike_count") || defKey.includes("_bulb_");
  }
  if (kind === "bulbs") {
    return defKey.includes("_spike_");
  }
  return true;
}

/**
 * Per-zone geometry extras (``extra_zone_*``) + finish/hex for extra sub-meshes.
 */
export function ZoneExtraControls({ slug, showEmptyHint }: Props) {
  const defs = useAppStore((st) => st.animatedBuildControls[slug] ?? EMPTY_DEFS);
  const values = useAppStore((st) => st.animatedBuildOptionValues[slug] ?? EMPTY_VALUES);
  const setAnimatedBuildOption = useAppStore((st) => st.setAnimatedBuildOption);

  const { zones, byZone, hasAny } = partitionZoneExtraDefs(slug, defs);

  if (!hasAny) {
    if (!showEmptyHint) return null;
    return (
      <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
        <span style={titleStyle}>Geometry extras</span>
        <div style={{ color: "#9d9d9d", fontSize: 11 }}>
          No extra geometry controls for this enemy (check meta / build API).
        </div>
      </div>
    );
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
      <span style={{ ...titleStyle, fontWeight: 600 }}>Geometry extras (per zone)</span>
      {zones.map((zone) => {
        const zdefs = byZone[zone] ?? [];
        if (zdefs.length === 0) return null;
        const kindKey = `extra_zone_${zone}_kind`;
        const rawKind = typeof values[kindKey] === "string" ? (values[kindKey] as string) : "none";
        const kind = effectiveKind(zone, rawKind);
        const allowedKinds = kindOptionsForZone(zone);
        const kindDef = zdefs.find((d) => d.key === kindKey);

        return (
          <details key={zone} open style={{ borderTop: "1px solid #3c3c3c", paddingTop: 8 }}>
            <summary style={{ ...titleStyle, fontSize: 11, color: "#858585", cursor: "pointer" }}>
              Zone: {zone.replace("_", " ")}
            </summary>
            <div style={{ display: "flex", flexDirection: "column", gap: 6, marginTop: 8 }}>
              {kindDef && kindDef.type === "select_str" ? (
                <label style={{ display: "flex", gap: 4, alignItems: "center", flexWrap: "wrap" }}>
                  <span style={rowStyles.label}>{kindDef.label}</span>
                  <select
                    style={rowStyles.select}
                    value={kind}
                    onChange={(e) => setAnimatedBuildOption(slug, kindKey, e.target.value)}
                    aria-label={`${zone} extra kind`}
                  >
                    {allowedKinds.map((opt) => (
                      <option key={opt} value={opt}>
                        {opt}
                      </option>
                    ))}
                  </select>
                  {zone !== "head" ? (
                    <span style={{ fontSize: 10, color: "#858585" }}>Horns use the head zone only.</span>
                  ) : null}
                </label>
              ) : null}
              {zdefs.map((def) => {
                if (def.key === kindKey) return null;
                const dis = rowDisabled(kind, def.key);
                return (
                  <div
                    key={def.key}
                    style={{
                      opacity: dis ? 0.42 : 1,
                      pointerEvents: dis ? "none" : undefined,
                    }}
                  >
                    <ControlRow
                      def={def}
                      value={values[def.key]}
                      onChange={(v) => setAnimatedBuildOption(slug, def.key, v)}
                    />
                  </div>
                );
              })}
            </div>
          </details>
        );
      })}
    </div>
  );
}
