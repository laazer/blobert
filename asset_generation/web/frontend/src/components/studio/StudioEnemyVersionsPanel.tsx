import { useState } from "react";
import type { RegistryEnemyVersion } from "../../types";
import type { EnemyDeletePlan } from "../Editor/registryEnemyTypes";
import { RegistryEnemyLoadExistingSection } from "../Editor/RegistryEnemyLoadExistingSection";
import type { LoadExistingCandidate } from "../../api/client";
import { STUDIO_INK_MUTED } from "../../styles/studioTokens";
import { StudioVersionList } from "./StudioVersionList";
import { StudioVersionSlotsSection } from "./StudioVersionSlotsSection";

export type StudioEnemyVersionsPanelProps = {
  family: string;
  versions: RegistryEnemyVersion[];
  slotVersionIds: string[];
  activeVersionId: string | null;
  addSlotDisabled: boolean;
  addSlotPreparing: boolean;
  slotSaveBusy: boolean;
  busyKey: string | null;
  deleteBusyKey: string | null;
  loadExistingCandidates: LoadExistingCandidate[];
  loadExistingSelection: string;
  loadExistingBusy: boolean;
  knownTags: readonly string[];
  hideDisplayTags: ReadonlySet<string>;
  onAddSlot: (family: string) => void;
  onAddEmptySlot: (family: string) => void;
  onRemoveSlot: (family: string, index: number) => void;
  onUpdateSlotVersion: (family: string, index: number, versionId: string) => void;
  onSaveSlots: (family: string) => void;
  onApplyFlags: (family: string, v: RegistryEnemyVersion, nextDraft: boolean, nextInUse: boolean) => void;
  onPreviewVersion: (family: string, v: RegistryEnemyVersion) => void;
  onDeleteVersion: (family: string, v: RegistryEnemyVersion) => void;
  getEnemyDeletePlan: (family: string, v: RegistryEnemyVersion) => EnemyDeletePlan | null;
  onPatchTags: (family: string, v: RegistryEnemyVersion, tags: string[]) => void | Promise<void>;
  onLoadExistingSelectionChange: (key: string) => void;
  onLoadExistingInPreview: () => void;
};

export function StudioEnemyVersionsPanel({
  family,
  versions,
  slotVersionIds,
  activeVersionId,
  addSlotDisabled,
  addSlotPreparing,
  slotSaveBusy,
  busyKey,
  deleteBusyKey,
  loadExistingCandidates,
  loadExistingSelection,
  loadExistingBusy,
  knownTags,
  hideDisplayTags,
  onAddSlot,
  onAddEmptySlot,
  onRemoveSlot,
  onUpdateSlotVersion,
  onSaveSlots,
  onApplyFlags,
  onPreviewVersion,
  onDeleteVersion,
  getEnemyDeletePlan,
  onPatchTags,
  onLoadExistingSelectionChange,
  onLoadExistingInPreview,
}: StudioEnemyVersionsPanelProps) {
  const [compareVersionIds, setCompareVersionIds] = useState<string[]>([]);
  const pendingVersionId = busyKey ?? deleteBusyKey;

  return (
    <div data-testid={`studio-enemy-versions-${family}`}>
      <StudioVersionList
        family={family}
        versions={versions}
        activeVersionId={activeVersionId}
        compareVersionIds={compareVersionIds}
        onCompareVersionIdsChange={setCompareVersionIds}
        pendingVersionId={pendingVersionId}
        knownTags={knownTags}
        hideDisplayTags={hideDisplayTags}
        getDeletePlan={(row) => getEnemyDeletePlan(family, row)}
        onSelectVersion={(row) => onPreviewVersion(family, row)}
        onApplyPool={(row, draft, inUse) => onApplyFlags(family, row, draft, inUse)}
        onDeleteVersion={(row) => onDeleteVersion(family, row)}
        onPatchTags={(row, tags) => onPatchTags(family, row, tags)}
        onNewVersion={() => onAddSlot(family)}
        newVersionDisabled={addSlotDisabled}
        newVersionBusy={addSlotPreparing}
      />

      <details data-testid="studio-version-slots-details" style={{ marginTop: 14 }}>
        <summary
          style={{
            cursor: "pointer",
            fontSize: 11,
            fontWeight: 600,
            color: STUDIO_INK_MUTED,
            userSelect: "none",
          }}
        >
          Spawn pool slots
        </summary>
        <StudioVersionSlotsSection
          family={family}
          versions={versions}
          slotVersionIds={slotVersionIds}
          busy={slotSaveBusy}
          addSlotDisabled={addSlotDisabled}
          addSlotPreparing={addSlotPreparing}
          onAddSlot={() => onAddSlot(family)}
          onAddEmptySlot={() => onAddEmptySlot(family)}
          onRemoveSlot={(idx) => onRemoveSlot(family, idx)}
          onUpdateSlotVersion={(idx, versionId) => onUpdateSlotVersion(family, idx, versionId)}
          onSaveSlots={() => onSaveSlots(family)}
        />
      </details>

      {loadExistingCandidates.length > 0 ? (
        <details data-testid="studio-version-load-existing-details" style={{ marginTop: 10 }}>
          <summary
            style={{
              cursor: "pointer",
              fontSize: 11,
              fontWeight: 600,
              color: STUDIO_INK_MUTED,
              userSelect: "none",
            }}
          >
            Load from disk
          </summary>
          <div style={{ marginTop: 10 }}>
            <RegistryEnemyLoadExistingSection
              loadExistingCandidates={loadExistingCandidates}
              loadExistingSelection={loadExistingSelection}
              onLoadExistingSelectionChange={onLoadExistingSelectionChange}
              loadExistingBusy={loadExistingBusy}
              onLoadExistingInPreview={onLoadExistingInPreview}
              activeFamily={family}
            />
          </div>
        </details>
      ) : null}
    </div>
  );
}
