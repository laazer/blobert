import { useState } from "react";
import { ELEMENTS } from "../../constants/elements";
import type { RegistryEnemyVersion } from "../../types";
import type { EnemyDeletePlan } from "../Editor/registryEnemyTypes";
import {
  versionElementId,
  versionGlbLabel,
  versionPoolKind,
  type VersionPoolKind,
} from "../../utils/studioVersionUi";
import { STUDIO_INK_MUTED, STUDIO_INK_PRIMARY, STUDIO_NEUTRAL_ACCENT } from "../../styles/studioTokens";
import { studioVersionCardStyle, studioVersionMetaMono } from "./studioVersionStyles";
import { StudioVersionRowMenu } from "./StudioVersionRowMenu";
import { StudioVersionTags } from "./StudioVersionTags";
import { StudioVersionThumb } from "./StudioVersionThumb";

type Props = {
  family: string;
  row: RegistryEnemyVersion;
  familyVersions: readonly RegistryEnemyVersion[];
  active: boolean;
  inCompare: boolean;
  compareMode: boolean;
  pending: boolean;
  tagIndentPx: number;
  knownTags: readonly string[];
  hideDisplayTags: ReadonlySet<string>;
  deletePlan: EnemyDeletePlan | null;
  onSelect: () => void;
  onToggleCompare: () => void;
  onTogglePool: (row: RegistryEnemyVersion, next: VersionPoolKind) => void;
  onDelete: () => void;
  onPatchTags: (tags: string[]) => void | Promise<void>;
};

const poolDotColor: Record<VersionPoolKind, string> = {
  pool: "#4cb87d",
  draft: "#ffd23d",
  none: "#5a5a66",
};

export function StudioVersionRow({
  family,
  row,
  familyVersions,
  active,
  inCompare,
  compareMode,
  pending,
  tagIndentPx,
  knownTags,
  hideDisplayTags,
  deletePlan,
  onSelect,
  onToggleCompare,
  onTogglePool,
  onDelete,
  onPatchTags,
}: Props) {
  const [menuOpen, setMenuOpen] = useState(false);
  const elementId = versionElementId(family, row, familyVersions);
  const hue = ELEMENTS[elementId].hue;
  const poolKind = versionPoolKind(row);
  const displayName = row.name?.trim();

  return (
    <div
      style={studioVersionCardStyle({ active, inCompare, accentHue: hue })}
      data-testid={`studio-version-row-${row.id}`}
    >
      <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
        {compareMode ? (
          <button
            type="button"
            aria-label={inCompare ? `Remove ${row.id} from compare` : `Add ${row.id} to compare`}
            aria-pressed={inCompare}
            disabled={pending}
            data-testid={`studio-version-compare-${row.id}`}
            style={{
              width: 18,
              height: 18,
              borderRadius: 4,
              background: inCompare ? STUDIO_NEUTRAL_ACCENT : "transparent",
              border: inCompare ? "none" : "1.5px solid rgba(255,255,255,0.2)",
              color: "#0c0c10",
              cursor: pending ? "wait" : "pointer",
              padding: 0,
              fontSize: 11,
              fontWeight: 800,
              flexShrink: 0,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
            onClick={(ev) => {
              ev.stopPropagation();
              onToggleCompare();
            }}
          >
            {inCompare ? "✓" : null}
          </button>
        ) : null}
        <button
          type="button"
          disabled={pending}
          onClick={onSelect}
          style={{
            display: "flex",
            alignItems: "center",
            gap: 10,
            flex: 1,
            minWidth: 0,
            padding: 0,
            border: "none",
            background: "transparent",
            cursor: pending ? "wait" : "pointer",
            textAlign: "left",
          }}
        >
          <StudioVersionThumb hue={hue} title={row.id} />
          <span style={{ flex: 1, minWidth: 0 }}>
            <span
              style={{
                display: "block",
                fontSize: 12,
                fontWeight: 600,
                color: STUDIO_INK_PRIMARY,
                overflow: "hidden",
                textOverflow: "ellipsis",
                whiteSpace: "nowrap",
              }}
            >
              {displayName ? (
                displayName
              ) : (
                <span style={{ color: STUDIO_INK_MUTED, fontStyle: "italic" }}>untitled</span>
              )}
            </span>
            <span style={studioVersionMetaMono}>{versionGlbLabel(row.id)}</span>
          </span>
        </button>
        <span
          title={poolKind === "pool" ? "In pool" : poolKind === "draft" ? "Draft" : "Not in pool"}
          aria-label={poolKind === "pool" ? "In pool" : poolKind === "draft" ? "Draft" : "Not in pool"}
          style={{
            width: 6,
            height: 6,
            borderRadius: "50%",
            flexShrink: 0,
            background: poolDotColor[poolKind],
            boxShadow: poolKind === "none" ? "none" : `0 0 6px ${poolDotColor[poolKind]}`,
          }}
        />
        <button
          type="button"
          title="More actions"
          aria-label={`Actions for ${row.id}`}
          aria-expanded={menuOpen}
          disabled={pending}
          data-testid={`studio-version-menu-${row.id}`}
          style={{
            width: 22,
            height: 22,
            borderRadius: 5,
            background: menuOpen ? "rgba(255,255,255,0.08)" : "transparent",
            border: 0,
            color: "#8a8a96",
            cursor: pending ? "wait" : "pointer",
            padding: 0,
            fontSize: 14,
            lineHeight: 1,
            flexShrink: 0,
          }}
          onClick={(ev) => {
            ev.stopPropagation();
            setMenuOpen((o) => !o);
          }}
        >
          ⋯
        </button>
      </div>

      <StudioVersionTags
        family={family}
        version={row}
        knownTags={knownTags}
        hideDisplayTags={hideDisplayTags}
        disabled={pending}
        tagIndentPx={tagIndentPx}
        onCommit={onPatchTags}
      />

      {menuOpen ? (
        <StudioVersionRowMenu
          poolKind={poolKind}
          canDelete={deletePlan != null}
          onClose={() => setMenuOpen(false)}
          onDuplicate={() => setMenuOpen(false)}
          onCompare={() => {
            onToggleCompare();
            setMenuOpen(false);
          }}
          onTogglePool={() => {
            if (poolKind === "pool") onTogglePool(row, "draft");
            else onTogglePool(row, "pool");
            setMenuOpen(false);
          }}
          onDelete={() => {
            onDelete();
            setMenuOpen(false);
          }}
        />
      ) : null}
    </div>
  );
}
