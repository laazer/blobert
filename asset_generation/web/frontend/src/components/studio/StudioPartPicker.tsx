import type { CoarseZoneKey } from "../../utils/elementColorPalettes";
import { normalizedColorMode } from "../Preview/ZoneTextureBlock";
import type { GradientDirection } from "../ColorPicker/common/DirectionSelector";
import { readZoneHex, zoneToPartLabel } from "../../utils/studioLookMaterial";
import { STUDIO_SURFACE_PANEL } from "../../styles/studioTokens";
import { gradientPreviewCss } from "./studioMaterialSphere";
import { StudioMaterialSpherePreview } from "./StudioMaterialSpherePreview";
import type { MaterialSphereVariant } from "./studioMaterialSphere";

type Props = {
  zones: readonly CoarseZoneKey[];
  activeZone: CoarseZoneKey;
  elementHue: string;
  values: Readonly<Record<string, unknown>>;
  onSelectZone: (zone: CoarseZoneKey) => void;
};

export function StudioPartPicker({ zones, activeZone, elementHue, values, onSelectZone }: Props) {
  const columns = Math.min(zones.length, 5);

  return (
    <div
      data-testid="studio-look-part-picker"
      style={{
        display: "grid",
        gridTemplateColumns: `repeat(${columns}, 1fr)`,
        gap: 5,
      }}
    >
      {zones.map((zone) => {
        const label = zoneToPartLabel(zone);
        const active = activeZone === zone;
        const hex = readZoneHex(values, zone) || "#888888";
        const colorMode = normalizedColorMode(zone, values);
        const materialVariant: MaterialSphereVariant =
          colorMode === "image" ? "image" : colorMode === "gradient" ? "gradient" : "solid";
        const gradA = values[`feat_${zone}_color_a`];
        const gradB = values[`feat_${zone}_color_b`];
        const gradDir = values[`feat_${zone}_color_direction`];
        const gradientCss =
          materialVariant === "gradient" &&
          typeof gradA === "string" &&
          typeof gradB === "string"
            ? gradientPreviewCss(
                gradA,
                gradB,
                (typeof gradDir === "string" ? gradDir : "horizontal") as GradientDirection,
              )
            : undefined;

        return (
          <button
            key={zone}
            type="button"
            data-testid={`studio-look-part-chip-${zone}`}
            aria-pressed={active}
            onClick={() => onSelectZone(zone)}
            style={{
              position: "relative",
              padding: "10px 6px 8px",
              borderRadius: 8,
              background: active ? "rgba(255,255,255,0.04)" : STUDIO_SURFACE_PANEL,
              border: active ? `1.5px solid ${elementHue}` : "1px solid rgba(255,255,255,0.06)",
              cursor: "pointer",
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              gap: 5,
              boxShadow: active ? `0 4px 14px ${elementHue}30` : "none",
            }}
          >
            <StudioMaterialSpherePreview
              variant={materialVariant}
              color={hex.startsWith("#") ? hex : `#${hex.replace(/^#/, "")}`}
              gradientCss={gradientCss}
              accentHue={elementHue}
              size={26}
              title={`${label} material`}
            />
            <div
              style={{
                fontSize: 10.5,
                fontWeight: 700,
                color: active ? "#ededf0" : "#bababf",
                letterSpacing: 0.2,
              }}
            >
              {label}
            </div>
            {active ? (
              <span
                style={{
                  position: "absolute",
                  top: 6,
                  right: 6,
                  fontSize: 8,
                  fontWeight: 800,
                  letterSpacing: 0.6,
                  color: elementHue,
                  textTransform: "uppercase",
                }}
              >
                edit
              </span>
            ) : null}
          </button>
        );
      })}
    </div>
  );
}
