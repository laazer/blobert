import type { CoarseZoneKey } from "../../utils/elementColorPalettes";
import {
  finishPillSelected,
  readZoneFinish,
  STUDIO_BODY_FINISH_PILLS,
} from "../../utils/studioLookMaterial";
import { STUDIO_INK_MUTED, STUDIO_INK_PRIMARY, STUDIO_SURFACE_PANEL } from "../../styles/studioTokens";

type Props = {
  zone: CoarseZoneKey;
  values: Readonly<Record<string, unknown>>;
  knownDefKeys: ReadonlySet<string>;
  onFinishChange: (finish: string) => void;
};

export function StudioPartContextBar({ zone, values, knownDefKeys, onFinishChange }: Props) {
  const finishKey = `feat_${zone}_finish`;
  if (!knownDefKeys.has(finishKey)) return null;

  const stored = readZoneFinish(values, zone);

  return (
    <div
      data-testid={`studio-look-finish-bar-${zone}`}
      style={{
        marginTop: 8,
        display: "flex",
        alignItems: "center",
        gap: 10,
        padding: "0 4px",
      }}
    >
      <span
        style={{
          fontSize: 10,
          color: STUDIO_INK_MUTED,
          fontWeight: 600,
          letterSpacing: 0.6,
          textTransform: "uppercase",
        }}
      >
        Finish
      </span>
      <div
        style={{
          display: "flex",
          gap: 3,
          background: STUDIO_SURFACE_PANEL,
          padding: 2,
          borderRadius: 5,
          flex: 1,
        }}
      >
        {STUDIO_BODY_FINISH_PILLS.map((f) => {
          const active = finishPillSelected(stored, f);
          return (
            <button
              key={f}
              type="button"
              data-testid={`studio-look-finish-${zone}-${f}`}
              aria-pressed={active}
              onClick={() => onFinishChange(f)}
              style={{
                flex: 1,
                padding: "4px 8px",
                border: 0,
                borderRadius: 3,
                background: active ? "#23232e" : "transparent",
                color: active ? STUDIO_INK_PRIMARY : "#8a8a96",
                fontSize: 10.5,
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
  );
}
