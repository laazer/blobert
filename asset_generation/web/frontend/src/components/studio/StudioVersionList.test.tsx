// @vitest-environment jsdom
import { afterEach, describe, expect, it, vi } from "vitest";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import type { RegistryEnemyVersion } from "../../types";
import { StudioVersionList } from "./StudioVersionList";

const versions: RegistryEnemyVersion[] = [
  { id: "spider_animated_00", path: "animated_exports/spider_animated_00.glb", draft: false, in_use: true, name: "alpha" },
  { id: "spider_animated_01", path: "animated_exports/draft/spider_animated_01.glb", draft: true, in_use: false },
];

afterEach(() => cleanup());

describe("StudioVersionList", () => {
  it("renders v2 filter chips and version cards", () => {
    render(
      <StudioVersionList
        family="spider"
        versions={versions}
        activeVersionId="spider_animated_00"
        compareVersionIds={[]}
        onCompareVersionIdsChange={vi.fn()}
        pendingVersionId={null}
        knownTags={["spider", "fire"]}
        hideDisplayTags={new Set(["spider"])}
        getDeletePlan={() => null}
        onSelectVersion={vi.fn()}
        onApplyPool={vi.fn()}
        onDeleteVersion={vi.fn()}
        onPatchTags={vi.fn()}
        onNewVersion={vi.fn()}
      />,
    );

    expect(screen.getByTestId("studio-version-list")).toBeInTheDocument();
    expect(screen.getByTestId("studio-version-filter-pool")).toBeInTheDocument();
    expect(screen.getByTestId("studio-version-row-spider_animated_00")).toBeInTheDocument();
    expect(screen.getByText("alpha")).toBeInTheDocument();
  });

  it("filters to drafts only", () => {
    render(
      <StudioVersionList
        family="spider"
        versions={versions}
        activeVersionId={null}
        compareVersionIds={[]}
        onCompareVersionIdsChange={vi.fn()}
        pendingVersionId={null}
        knownTags={[]}
        hideDisplayTags={new Set()}
        getDeletePlan={() => null}
        onSelectVersion={vi.fn()}
        onApplyPool={vi.fn()}
        onDeleteVersion={vi.fn()}
        onPatchTags={vi.fn()}
        onNewVersion={vi.fn()}
      />,
    );

    fireEvent.click(screen.getByTestId("studio-version-filter-draft"));
    expect(screen.queryByTestId("studio-version-row-spider_animated_00")).toBeNull();
    expect(screen.getByTestId("studio-version-row-spider_animated_01")).toBeInTheDocument();
  });
});
