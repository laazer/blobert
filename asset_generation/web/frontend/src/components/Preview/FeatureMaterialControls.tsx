import { useAppStore } from "../../store/useAppStore";
import type { AnimatedBuildControlDef } from "../../types";
import { FEATURE_ZONES_BY_SLUG } from "../../utils/animatedZoneControlsMerge";
import { normalizeAnimatedSlug } from "../../utils/enemyDisplay";
import { ControlRow, rowStyles } from "./BuildControlRow";
import { ZONE_FINISH_HEX_RE, ZONE_TEXTURE_CONTROL_RE, partitionAnimatedFeatureDefs } from "./featureMaterialPartition";
import { ZoneTextureBlock } from "./ZoneTextureBlock";

/** Stable fallbacks so Zustand `useSyncExternalStore` snapshots do not change every tick (see React #getSnapshot). */
const EMPTY_DEFS: readonly AnimatedBuildControlDef[] = [];
const EMPTY_VALUES: Readonly<Record<string, unknown>> = {};

const titleStyle = rowStyles.label;

type Props = {
  slug: string;
  /** Tighter heading when embedded in a compact strip */
  compactTitle?: boolean;
  /** When no feat_* controls exist, show a short hint instead of rendering nothing */
  showEmptyHint?: boolean;
};

/**
 * Per-slot material finish + hex (feat_* keys from meta). Shared by Build panel and Command panel.
 */
export function FeatureMaterialControls({ slug, compactTitle, showEmptyHint }: Props) {
  const defs = useAppStore((st) => st.animatedBuildControls[slug] ?? EMPTY_DEFS);
  const values = useAppStore((st) => st.animatedBuildOptionValues[slug] ?? EMPTY_VALUES);
  const setAnimatedBuildOption = useAppStore((st) => st.setAnimatedBuildOption);

  const { featureDefs, zoneDefs, limbPartDefs, jointPartDefs } = partitionAnimatedFeatureDefs(defs);
  const zoneTextureDefs = defs.filter((d) => ZONE_TEXTURE_CONTROL_RE.test(d.key));
  const zones = FEATURE_ZONES_BY_SLUG[normalizeAnimatedSlug(slug)] ?? [];

  if (featureDefs.length === 0) {
    if (!showEmptyHint) return null;
    return (
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          gap: 6,
          padding: compactTitle ? "4px 0 0" : 0,
          borderTop: compactTitle ? "1px solid #3c3c3c" : undefined,
          marginTop: compactTitle ? 4 : 0,
        }}
      >
        <span style={{ ...titleStyle, fontWeight: compactTitle ? 600 : undefined }}>
          Part materials (zones + limb / joint overrides)
        </span>
        <div style={{ color: "#9d9d9d", fontSize: 11 }}>
          No per-part color controls for this enemy (check meta / build API).
        </div>
      </div>
    );
  }

  const row = (def: AnimatedBuildControlDef) => (
    <ControlRow
      key={def.key}
      def={def}
      value={values[def.key]}
      onChange={(v) => setAnimatedBuildOption(slug, def.key, v)}
    />
  );

  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        gap: 6,
        padding: compactTitle ? "4px 0 0" : 0,
        borderTop: compactTitle ? "1px solid #3c3c3c" : undefined,
        marginTop: compactTitle ? 4 : 0,
      }}
    >
      <span style={{ ...titleStyle, fontWeight: compactTitle ? 600 : undefined }}>
        Part materials (zones + limb / joint overrides)
      </span>
      <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
        <span style={{ ...titleStyle, fontSize: 10, color: "#858585" }}>Zones</span>
        {zones.map((zone) => {
          const zFinish = zoneDefs.filter((d) => {
            const m = ZONE_FINISH_HEX_RE.exec(d.key);
            return m && m[1] === zone;
          });
          const zTex = zoneTextureDefs.filter((d) => d.key.startsWith(`feat_${zone}_texture_`));
          return (
            <div
              key={zone}
              style={{
                display: "flex",
                flexDirection: "column",
                gap: 6,
                paddingBottom: 8,
                marginBottom: 4,
                borderBottom: "1px solid #2d2d2d",
              }}
            >
              <ZoneTextureBlock zone={zone} slug={slug} defs={zTex} finishHexDefs={zFinish} />
            </div>
          );
        })}
        {limbPartDefs.length > 0 ? (
          <details style={{ marginTop: 2 }}>
            <summary style={{ ...titleStyle, fontSize: 10, color: "#858585", cursor: "pointer" }}>
              Per-limb overrides ({limbPartDefs.length})
            </summary>
            <div style={{ display: "flex", flexDirection: "column", gap: 6, marginTop: 6 }}>
              {limbPartDefs.map(row)}
            </div>
          </details>
        ) : null}
        {jointPartDefs.length > 0 ? (
          <details style={{ marginTop: 2 }}>
            <summary style={{ ...titleStyle, fontSize: 10, color: "#858585", cursor: "pointer" }}>
              Per-joint overrides ({jointPartDefs.length})
            </summary>
            <div style={{ display: "flex", flexDirection: "column", gap: 6, marginTop: 6 }}>
              {jointPartDefs.map(row)}
            </div>
          </details>
        ) : null}
      </div>
    </div>
  );
}
