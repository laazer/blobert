import { afterEach, describe, expect, it, vi } from "vitest";
import {
  fetchLoadExistingCandidates,
  fetchEnemyFamilySlots,
  openExistingRegistryModel,
  patchRegistryPlayerActiveVisual,
  putEnemyFamilySlots,
} from "./client";

describe("registry model-selection client contracts", () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it("PATCH player_active_visual sends exact payload and returns JSON", async () => {
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(
        new Response(
          JSON.stringify({
            schema_version: 1,
            enemies: {},
            player_active_visual: { path: "player_exports/blobert_blue_00.glb", draft: false },
          }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        ),
      );

    const out = await patchRegistryPlayerActiveVisual({
      path: "player_exports/blobert_blue_00.glb",
    });

    expect(fetchMock).toHaveBeenCalledWith("/api/registry/model/player_active_visual", {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ path: "player_exports/blobert_blue_00.glb" }),
    });
    expect(out.player_active_visual).toEqual({
      path: "player_exports/blobert_blue_00.glb",
      draft: false,
    });
  });

  it("PATCH player_active_visual rejects API validation errors", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify({ detail: "active player visual cannot be draft" }), {
        status: 400,
        headers: { "Content-Type": "application/json" },
      }),
    );

    await expect(
      patchRegistryPlayerActiveVisual({
        draft: true,
      }),
    ).rejects.toThrow();
  });

  it("PUT enemy slots sends full replacement version_ids and returns server payload", async () => {
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(
        new Response(
          JSON.stringify({
            family: "spider",
            version_ids: ["spider_animated_01", "spider_animated_00"],
            resolved_paths: [
              "animated_exports/spider_animated_01.glb",
              "animated_exports/spider_animated_00.glb",
            ],
          }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        ),
      );

    const out = await putEnemyFamilySlots("spider", ["spider_animated_01", "spider_animated_00"]);

    expect(fetchMock).toHaveBeenCalledWith("/api/registry/model/enemies/spider/slots", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ version_ids: ["spider_animated_01", "spider_animated_00"] }),
    });
    expect(out).toEqual({
      family: "spider",
      version_ids: ["spider_animated_01", "spider_animated_00"],
      resolved_paths: [
        "animated_exports/spider_animated_01.glb",
        "animated_exports/spider_animated_00.glb",
      ],
    });
  });

  it("GET enemy slots returns the persisted server state", async () => {
    const fetchMock = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(
        new Response(
          JSON.stringify({
            family: "spider",
            version_ids: ["spider_animated_00"],
            resolved_paths: ["animated_exports/spider_animated_00.glb"],
          }),
          { status: 200, headers: { "Content-Type": "application/json" } },
        ),
      );

    const out = await fetchEnemyFamilySlots("spider");
    expect(fetchMock).toHaveBeenCalledWith("/api/registry/model/enemies/spider/slots");
    expect(out.version_ids).toEqual(["spider_animated_00"]);
  });

  it("PUT enemy slots surfaces 400 validation errors (draft/duplicate)", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify({ detail: "duplicate version_ids are not allowed" }), {
        status: 400,
        headers: { "Content-Type": "application/json" },
      }),
    );

    await expect(putEnemyFamilySlots("spider", ["spider_animated_00", "spider_animated_00"])).rejects.toThrow();
  });

  it("PUT enemy slots surfaces 404 errors (unknown family or version)", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify({ detail: "unknown family: not_real" }), {
        status: 404,
        headers: { "Content-Type": "application/json" },
      }),
    );

    await expect(putEnemyFamilySlots("not_real", ["spider_animated_00"])).rejects.toThrow();
  });

  it("GET load-existing candidates returns deterministic candidate payload", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(
        JSON.stringify({
          candidates: [
            {
              kind: "enemy",
              family: "alpha",
              version_id: "alpha_live_00",
              path: "animated_exports/alpha_live_00.glb",
            },
            {
              kind: "player",
              path: "player_exports/blobert_blue_00.glb",
            },
          ],
        }),
        { status: 200, headers: { "Content-Type": "application/json" } },
      ),
    );

    const out = await fetchLoadExistingCandidates();
    expect(fetchMock).toHaveBeenCalledWith("/api/registry/model/load_existing/candidates");
    expect(out.candidates).toEqual([
      {
        kind: "enemy",
        family: "alpha",
        version_id: "alpha_live_00",
        path: "animated_exports/alpha_live_00.glb",
      },
      {
        kind: "player",
        path: "player_exports/blobert_blue_00.glb",
      },
    ]);
  });

  it("POST load-existing open sends registry identity payload and returns resolved path", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(
        JSON.stringify({
          kind: "enemy",
          family: "alpha",
          version_id: "alpha_live_00",
          path: "animated_exports/alpha_live_00.glb",
        }),
        { status: 200, headers: { "Content-Type": "application/json" } },
      ),
    );

    const out = await openExistingRegistryModel({
      kind: "enemy",
      family: "alpha",
      version_id: "alpha_live_00",
    });
    expect(fetchMock).toHaveBeenCalledWith("/api/registry/model/load_existing/open", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        kind: "enemy",
        family: "alpha",
        version_id: "alpha_live_00",
      }),
    });
    expect(out.path).toBe("animated_exports/alpha_live_00.glb");
  });

  it("POST load-existing open surfaces deterministic rejection errors (400/403/404)", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify({ detail: "forbidden target path class: absolute-path" }), {
        status: 403,
        headers: { "Content-Type": "application/json" },
      }),
    );

    await expect(
      openExistingRegistryModel({
        kind: "path",
        path: "/abs/path.glb",
      }),
    ).rejects.toThrow();
  });
});
