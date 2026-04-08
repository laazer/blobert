import { useAppStore } from "../../store/useAppStore";
import type { AnimatedBuildControlDef } from "../../types";
import { ControlRow, rowStyles } from "./BuildControlRow";

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

  const featureDefs = defs.filter((d) => d.key.startsWith("feat_"));
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
          Part materials (body / head / limbs / extra)
        </span>
        <div style={{ color: "#9d9d9d", fontSize: 11 }}>
          No per-part color controls for this enemy (check meta / build API).
        </div>
      </div>
    );
  }

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
        Part materials (body / head / limbs / extra)
      </span>
      <div style={{ display: "flex", flexDirection: "column", gap: 6 }}>
        {featureDefs.map((def) => (
          <ControlRow
            key={def.key}
            def={def}
            value={values[def.key]}
            onChange={(v) => setAnimatedBuildOption(slug, def.key, v)}
          />
        ))}
      </div>
    </div>
  );
}
