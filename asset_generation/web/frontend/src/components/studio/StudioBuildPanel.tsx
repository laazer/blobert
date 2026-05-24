import { useMemo, useState, type CSSProperties, type ReactNode } from "react";
import { mergeBuildOptionValues } from "../../api/client";
import { useAppStore } from "../../store/useAppStore";
import type { AnimatedBuildControlDef } from "../../types";
import {
  BUILD_SECTION_DEFAULT_OPEN,
  BUILD_SECTION_LABEL,
  BUILD_SECTION_ORDER,
  eyesDefsWithoutPupil,
  partitionBuildControls,
  pupilControlDefs,
  summarizeBuildSection,
  type BuildSectionId,
} from "../../utils/buildControlSections";
import { STUDIO_INK_MUTED, STUDIO_INK_SECONDARY } from "../../styles/studioTokens";
import { StudioPanelHead } from "./StudioPanelHead";
import { StudioBuildControlRow } from "./StudioBuildControlRow";
import { StudioBuildSection } from "./StudioBuildSection";
import { StudioBuildSlider } from "./StudioBuildSlider";
import { studioBuildFilterInput } from "./studioBuildStyles";

type Props = {
  slug: string;
  defs: readonly AnimatedBuildControlDef[];
  values: Readonly<Record<string, unknown>>;
  accentHue: string;
  isRowDisabled: (key: string) => boolean;
  onChange: (key: string, value: number | string | boolean) => void;
  meshPartTree: ReactNode;
};

function boolControlValue(
  values: Readonly<Record<string, unknown>>,
  def: Extract<AnimatedBuildControlDef, { type: "bool" }>,
): boolean {
  const v = values[def.key];
  return typeof v === "boolean" ? v : def.default;
}

export function StudioBuildPanel({
  slug,
  defs,
  values,
  accentHue,
  isRowDisabled,
  onChange,
  meshPartTree,
}: Props) {
  const [filter, setFilter] = useState("");
  const animatedBuildControls = useAppStore((s) => s.animatedBuildControls);
  const applyAnimatedBuildOptionsForSlug = useAppStore((s) => s.applyAnimatedBuildOptionsForSlug);

  const q = filter.trim().toLowerCase();
  const filteredDefs = useMemo(
    () =>
      q
        ? defs.filter(
            (d) => d.key.toLowerCase().includes(q) || d.label.toLowerCase().includes(q),
          )
        : defs,
    [defs, q],
  );

  const sections = useMemo(() => partitionBuildControls(filteredDefs), [filteredDefs]);

  function resetOptions() {
    const merged = mergeBuildOptionValues(animatedBuildControls, {});
    const row = merged[slug];
    if (row) applyAnimatedBuildOptionsForSlug(slug, row);
  }

  function renderDef(def: AnimatedBuildControlDef) {
    if (def.type === "float") {
      return (
        <StudioBuildSlider
          key={def.key}
          def={def}
          value={values[def.key]}
          accentHue={accentHue}
          disabled={isRowDisabled(def.key)}
          showHint={false}
          onChange={(v) => onChange(def.key, v)}
        />
      );
    }
    return (
      <StudioBuildControlRow
        key={def.key}
        def={def}
        value={values[def.key]}
        accentHue={accentHue}
        disabled={isRowDisabled(def.key)}
        onChange={(v) => onChange(def.key, v)}
      />
    );
  }

  function renderSectionBody(sectionId: BuildSectionId, sectionDefs: AnimatedBuildControlDef[]) {
    if (sectionDefs.length === 0) return null;

    if (sectionId === "eyes") {
      const main = eyesDefsWithoutPupil(sectionDefs);
      const pupil = pupilControlDefs(sectionDefs);
      const pupilToggleDef = pupil.find(
        (d): d is Extract<AnimatedBuildControlDef, { type: "bool" }> =>
          d.key === "pupil_enabled" && d.type === "bool",
      );
      const pupilEnabled = pupilToggleDef ? boolControlValue(values, pupilToggleDef) : false;
      return (
        <>
          {main.map(renderDef)}
          {pupil.length > 0 ? (
            <div
              data-testid="studio-build-pupil-nest"
              style={{
                marginTop: 4,
                padding: "10px 10px",
                borderRadius: 7,
                background: "#0e0e14",
                border: "1px solid rgba(255,255,255,0.04)",
                display: "flex",
                flexDirection: "column",
                gap: 12,
              }}
            >
              {pupil.map((def) => {
                if (def.key === "pupil_shape") {
                  return (
                    <div
                      key={def.key}
                      style={{
                        opacity: pupilEnabled ? 1 : 0.45,
                        pointerEvents: pupilEnabled ? undefined : "none",
                      }}
                    >
                      {renderDef(def)}
                    </div>
                  );
                }
                return renderDef(def);
              })}
            </div>
          ) : null}
        </>
      );
    }

    if (sectionId === "mouth" || sectionId === "tail") {
      const enabledKey = sectionId === "mouth" ? "mouth_enabled" : "tail_enabled";
      const toggleDef = sectionDefs.find(
        (d): d is Extract<AnimatedBuildControlDef, { type: "bool" }> =>
          d.key === enabledKey && d.type === "bool",
      );
      const enabled = toggleDef ? boolControlValue(values, toggleDef) : false;
      return sectionDefs.map((def) => {
        if (def.key === `${sectionId}_shape` || def.key === "tail_length") {
          return (
            <div
              key={def.key}
              style={{
                opacity: enabled ? 1 : 0.45,
                pointerEvents: enabled ? undefined : "none",
              }}
            >
              {renderDef(def)}
            </div>
          );
        }
        return renderDef(def);
      });
    }

    return sectionDefs.map(renderDef);
  }

  const visibleSections = BUILD_SECTION_ORDER.filter((id) => sections[id].length > 0);

  return (
    <div
      data-testid="studio-build-panel"
      style={{ display: "flex", flexDirection: "column", gap: 14 }}
    >
      <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", gap: 10 }}>
        <div style={{ flex: 1, minWidth: 0 }}>
          <StudioPanelHead title="Build options" subtitle="Procedural mesh & rig parameters" />
        </div>
        <div style={{ display: "flex", gap: 6, flexShrink: 0, paddingTop: 2 }}>
          <button
            type="button"
            data-testid="studio-build-filter-btn"
            style={headerBtnStyle}
            onClick={() => {
              const el = document.getElementById("studio-build-filter-input");
              el?.focus();
            }}
          >
            Filter
          </button>
          <button
            type="button"
            data-testid="studio-build-reset-btn"
            style={headerBtnStyle}
            onClick={resetOptions}
          >
            Reset
          </button>
        </div>
      </div>

      <input
        id="studio-build-filter-input"
        type="search"
        placeholder="Filter controls…"
        aria-label="Filter build controls"
        value={filter}
        style={{ ...studioBuildFilterInput, marginBottom: 0, maxWidth: "100%" }}
        onChange={(e) => setFilter(e.target.value)}
      />

      {visibleSections.length === 0 ? (
        <span style={{ color: STUDIO_INK_MUTED, fontSize: 11 }}>No controls match filter.</span>
      ) : (
        visibleSections.map((sectionId) => {
          const sectionDefs = sections[sectionId];
          const summary = summarizeBuildSection(sectionId, sectionDefs, values);
          const badge =
            sectionId === "eyes" && typeof values.eye_count === "number"
              ? values.eye_count
              : undefined;
          return (
            <StudioBuildSection
              key={sectionId}
              sectionId={sectionId}
              title={BUILD_SECTION_LABEL[sectionId]}
              summary={summary}
              defaultOpen={BUILD_SECTION_DEFAULT_OPEN[sectionId]}
              badge={badge}
            >
              {renderSectionBody(sectionId, sectionDefs)}
            </StudioBuildSection>
          );
        })
      )}

      {meshPartTree}
    </div>
  );
}

const headerBtnStyle: CSSProperties = {
  background: "#16161d",
  color: STUDIO_INK_SECONDARY,
  border: "1px solid rgba(255,255,255,0.06)",
  borderRadius: 6,
  padding: "4px 10px",
  fontSize: 11,
  fontWeight: 600,
  cursor: "pointer",
  fontFamily: "inherit",
};
