import { useMemo, useState } from "react";
import type { RegistryEnemyVersion } from "../../types";
import type { EnemyDeletePlan } from "../Editor/registryEnemyTypes";
import {
  matchesStudioVersionFilter,
  type StudioVersionFilter,
} from "../../utils/studioVersionUi";
import { STUDIO_INK_MUTED } from "../../styles/studioTokens";
import {
  STUDIO_COMPARE_MAX,
  STUDIO_VERSION_LIST_GAP_PX,
  STUDIO_VERSION_ROW_GAP_PX,
  studioCompareBarStyle,
  studioFilterChipStyle,
  studioSoftButtonStyle,
} from "./studioVersionStyles";
import { StudioVersionRow } from "./StudioVersionRow";

const FILTER_LABELS: { id: StudioVersionFilter; label: string }[] = [
  { id: "all", label: "All" },
  { id: "pool", label: "In pool" },
  { id: "draft", label: "Drafts" },
];

export type StudioVersionListProps = {
  family: string;
  versions: RegistryEnemyVersion[];
  activeVersionId: string | null;
  compareVersionIds: readonly string[];
  onCompareVersionIdsChange: (ids: string[]) => void;
  pendingVersionId: string | null;
  knownTags: readonly string[];
  hideDisplayTags: ReadonlySet<string>;
  getDeletePlan: (row: RegistryEnemyVersion) => EnemyDeletePlan | null;
  onSelectVersion: (row: RegistryEnemyVersion) => void;
  onApplyPool: (row: RegistryEnemyVersion, draft: boolean, inUse: boolean) => void;
  onDeleteVersion: (row: RegistryEnemyVersion) => void;
  onPatchTags: (row: RegistryEnemyVersion, tags: string[]) => void | Promise<void>;
  onNewVersion: () => void;
  newVersionDisabled?: boolean;
  newVersionBusy?: boolean;
};

export function StudioVersionList({
  family,
  versions,
  activeVersionId,
  compareVersionIds,
  onCompareVersionIdsChange,
  pendingVersionId,
  knownTags,
  hideDisplayTags,
  getDeletePlan,
  onSelectVersion,
  onApplyPool,
  onDeleteVersion,
  onPatchTags,
  onNewVersion,
  newVersionDisabled,
  newVersionBusy,
}: StudioVersionListProps) {
  const [filter, setFilter] = useState<StudioVersionFilter>("all");
  const [compareMode, setCompareMode] = useState(compareVersionIds.length > 0);

  const visible = useMemo(
    () => versions.filter((row) => matchesStudioVersionFilter(row, filter)),
    [versions, filter],
  );

  const compareSet = useMemo(() => new Set(compareVersionIds), [compareVersionIds]);

  const compareMessage =
    compareVersionIds.length === 0
      ? "Pick up to 4 versions to compare"
      : compareVersionIds.length === 1
        ? "Pick at least one more to compare"
        : `Comparing ${compareVersionIds.length} versions in preview`;

  const tagIndentPx = compareMode ? 28 : 42;

  function toggleCompare(versionId: string) {
    const has = compareSet.has(versionId);
    if (has) {
      onCompareVersionIdsChange(compareVersionIds.filter((id) => id !== versionId));
      return;
    }
    if (compareVersionIds.length >= STUDIO_COMPARE_MAX) return;
    onCompareVersionIdsChange([...compareVersionIds, versionId]);
  }

  return (
    <div
      data-testid="studio-version-list"
      style={{ display: "flex", flexDirection: "column", gap: STUDIO_VERSION_LIST_GAP_PX }}
    >
      <div style={{ display: "flex", gap: 4, alignItems: "center", flexWrap: "wrap" }}>
        {FILTER_LABELS.map(({ id, label }) => (
          <button
            key={id}
            type="button"
            style={studioFilterChipStyle(filter === id)}
            data-testid={`studio-version-filter-${id}`}
            onClick={() => setFilter(id)}
          >
            {label}
          </button>
        ))}
        <div style={{ flex: 1, minWidth: 8 }} />
        <button
          type="button"
          title="Compare versions side-by-side"
          style={studioSoftButtonStyle(compareMode)}
          data-testid="studio-version-compare-toggle"
          onClick={() => setCompareMode((m) => !m)}
        >
          <span aria-hidden>▥</span> Compare
        </button>
        <button
          type="button"
          style={{
            ...studioSoftButtonStyle(false),
            background: "#23232e",
          }}
          disabled={newVersionDisabled || newVersionBusy}
          data-testid="studio-version-new"
          onClick={onNewVersion}
        >
          {newVersionBusy ? "Scanning…" : "+ New"}
        </button>
      </div>

      {compareMode ? (
        <div style={studioCompareBarStyle} data-testid="studio-version-compare-bar">
          <span style={{ fontSize: 11, color: "#cdd3ff", fontWeight: 600 }}>{compareMessage}</span>
          <div style={{ flex: 1 }} />
          {compareVersionIds.length > 0 ? (
            <button
              type="button"
              style={{
                background: "transparent",
                border: 0,
                color: "#9aa6ff",
                fontSize: 11,
                fontWeight: 600,
                cursor: "pointer",
                padding: 0,
              }}
              onClick={() => onCompareVersionIdsChange([])}
            >
              Clear
            </button>
          ) : null}
        </div>
      ) : null}

      {visible.length === 0 ? (
        <p style={{ margin: 0, fontSize: 11, color: STUDIO_INK_MUTED }}>No versions match this filter.</p>
      ) : (
        <div style={{ display: "flex", flexDirection: "column", gap: STUDIO_VERSION_ROW_GAP_PX }}>
          {visible.map((row) => {
            const pending = pendingVersionId === `${family}:${row.id}`;
            return (
              <StudioVersionRow
                key={row.id}
                family={family}
                row={row}
                familyVersions={versions}
                active={activeVersionId === row.id}
                inCompare={compareSet.has(row.id)}
                compareMode={compareMode}
                pending={pending}
                tagIndentPx={tagIndentPx}
                knownTags={knownTags}
                hideDisplayTags={hideDisplayTags}
                deletePlan={getDeletePlan(row)}
                onSelect={() => onSelectVersion(row)}
                onToggleCompare={() => toggleCompare(row.id)}
                onTogglePool={(v, kind) => {
                  if (kind === "draft") onApplyPool(v, true, false);
                  else onApplyPool(v, false, true);
                }}
                onDelete={() => onDeleteVersion(row)}
                onPatchTags={(tags) => onPatchTags(row, tags)}
              />
            );
          })}
        </div>
      )}
    </div>
  );
}
