import { describe, expect, it, vi } from "vitest";
import {
  buildEnemyDeletePlan,
  DRAFT_DELETE_CONFIRM_COPY,
  executeEnemyDeleteFlow,
  IN_USE_DELETE_CONFIRM_COPY,
} from "./ModelRegistryPane";

const REGISTRY_FIXTURE = {
  schema_version: 1,
  enemies: {
    spider: {
      versions: [{ id: "spider_live_00", path: "animated_exports/spider_live_00.glb", draft: false, in_use: true }],
    },
  },
  player_active_visual: { path: "player_exports/blobert_blue_00.glb", draft: false },
};

describe("ModelRegistryPane delete flow contracts", () => {
  it("builds a draft delete request with file deletion enabled", () => {
    const plan = buildEnemyDeletePlan("spider", {
      id: "spider_draft_00",
      draft: true,
      in_use: false,
    });
    expect(plan).toEqual({
      confirmMessage: DRAFT_DELETE_CONFIRM_COPY,
      request: {
        confirm: true,
        delete_files: true,
        confirm_text: "delete draft spider spider_draft_00",
      },
    });
  });

  it("builds an in-use delete request with in-use confirmation text", () => {
    const plan = buildEnemyDeletePlan("spider", {
      id: "spider_live_00",
      draft: false,
      in_use: true,
    });
    expect(plan).toEqual({
      confirmMessage: IN_USE_DELETE_CONFIRM_COPY,
      request: {
        confirm: true,
        delete_files: false,
        confirm_text: "delete in-use spider spider_live_00",
      },
    });
  });

  it("requires confirmation and performs no API call on cancel", async () => {
    const onDelete = vi.fn();
    const onSuccess = vi.fn();
    const onError = vi.fn();
    const result = await executeEnemyDeleteFlow({
      family: "spider",
      version: { id: "spider_draft_00", draft: true, in_use: false },
      confirmDelete: () => false,
      onDelete,
      onSuccess,
      onError,
    });
    expect(result).toBe("cancelled");
    expect(onDelete).not.toHaveBeenCalled();
    expect(onSuccess).not.toHaveBeenCalled();
    expect(onError).not.toHaveBeenCalled();
  });

  it("preserves local editor state on failed delete by skipping success sync", async () => {
    const onSuccess = vi.fn();
    const onError = vi.fn();
    const result = await executeEnemyDeleteFlow({
      family: "spider",
      version: { id: "spider_live_00", draft: false, in_use: true },
      confirmDelete: () => true,
      onDelete: vi.fn().mockRejectedValue(new Error("cannot delete sole in-use enemy version")),
      onSuccess,
      onError,
    });
    expect(result).toBe("failed");
    expect(onSuccess).not.toHaveBeenCalled();
    expect(onError).toHaveBeenCalledWith("cannot delete sole in-use enemy version");
  });

  it("runs a deterministic single refresh cycle on successful delete", async () => {
    const onDelete = vi.fn().mockResolvedValue(REGISTRY_FIXTURE);
    const onSuccess = vi.fn().mockResolvedValue(undefined);
    const result = await executeEnemyDeleteFlow({
      family: "spider",
      version: { id: "spider_draft_00", draft: true, in_use: false },
      confirmDelete: () => true,
      onDelete,
      onSuccess,
      onError: vi.fn(),
    });
    expect(result).toBe("deleted");
    expect(onDelete).toHaveBeenCalledTimes(1);
    expect(onSuccess).toHaveBeenCalledTimes(1);
    expect(onSuccess).toHaveBeenCalledWith(REGISTRY_FIXTURE);
  });
});
