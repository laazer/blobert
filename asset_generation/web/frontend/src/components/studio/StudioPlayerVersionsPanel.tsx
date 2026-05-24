import type { RegistryEnemyVersion } from "../../types";
import { StudioPanelHead } from "./StudioPanelHead";
import { StudioVersionList } from "./StudioVersionList";
import { playerColorLabel } from "../../utils/studioPlayerLibrary";

export type StudioPlayerVersionsPanelProps = {
  color: string;
  versions: readonly RegistryEnemyVersion[];
  activeVersionId: string | null;
  pendingVersionId: string | null;
  knownTags: readonly string[];
  hideDisplayTags: ReadonlySet<string>;
  scanBusy: boolean;
  onSelectVersion: (row: RegistryEnemyVersion) => void;
  onApplyFlags: (row: RegistryEnemyVersion, nextDraft: boolean, nextInUse: boolean) => void;
  onPatchTags: (row: RegistryEnemyVersion, tags: string[]) => void | Promise<void>;
  onScanExports: () => void;
};

export function StudioPlayerVersionsPanel({
  color,
  versions,
  activeVersionId,
  pendingVersionId,
  knownTags,
  hideDisplayTags,
  scanBusy,
  onSelectVersion,
  onApplyFlags,
  onPatchTags,
  onScanExports,
}: StudioPlayerVersionsPanelProps) {
  const label = playerColorLabel(color);

  return (
    <div data-testid={`studio-player-versions-${color}`}>
      <StudioPanelHead
        title="Versions"
        subtitle={`${label} slime — spawn pool and version rows`}
      />
      <StudioVersionList
        family="player"
        versions={versions}
        activeVersionId={activeVersionId}
        compareVersionIds={[]}
        onCompareVersionIdsChange={() => {}}
        pendingVersionId={pendingVersionId}
        knownTags={knownTags}
        hideDisplayTags={hideDisplayTags}
        getDeletePlan={() => null}
        onSelectVersion={onSelectVersion}
        onApplyPool={(row, draft, inUse) => onApplyFlags(row, draft, inUse)}
        onDeleteVersion={() => {}}
        onPatchTags={(_row, tags) => onPatchTags(_row, tags)}
        onNewVersion={onScanExports}
        newVersionDisabled={scanBusy}
        newVersionBusy={scanBusy}
        newVersionButtonLabel="Sync exports"
        newVersionBusyLabel="Syncing…"
      />
    </div>
  );
}
