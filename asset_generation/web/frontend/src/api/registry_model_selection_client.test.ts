import { afterEach, describe, expect, it, vi } from "vitest";
import {
  deleteRegistryEnemyVersion,
  deleteRegistryPlayerActiveVisual,
  fetchLoadExistingCandidates,
  fetchEnemyFamilySlots,
  fetchPlayerFamilySlots,
  openExistingRegistryModel,
  patchRegistryPlayerActiveVisual,
  postSyncDiscoveredAnimatedGlbVersions,
  putEnemyFamilySlots,
  putPlayerFamilySlots,
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

  it("POST sync_animated_exports registers on-disk GLBs and returns full manifest", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(
        JSON.stringify({
          schema_version: 1,
          enemies: {
            slug: {
              versions: [
                {
                  id: "slug_animated_00",
                  path: "animated_exports/slug_animated_00.glb",
                  draft: false,
                  in_use: true,
                },
                {
                  id: "slug_animated_01",
                  path: "animated_exports/slug_animated_01.glb",
                  draft: true,
                  in_use: false,
                },
              ],
            },
          },
          player_active_visual: null,
        }),
        { status: 200, headers: { "Content-Type": "application/json" } },
      ),
    );

    const out = await postSyncDiscoveredAnimatedGlbVersions("slug");

    expect(fetchMock).toHaveBeenCalledWith("/api/registry/model/enemies/slug/sync_animated_exports", {
      method: "POST",
    });
    expect(out.enemies.slug.versions).toHaveLength(2);
    expect(out.enemies.slug.versions[1].id).toBe("slug_animated_01");
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

  it("GET player slots returns persisted server state", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(
        JSON.stringify({
          family: "player",
          version_ids: ["player_slime_blue_00", ""],
          resolved_paths: ["player_exports/player_slime_blue_00.glb"],
        }),
        { status: 200, headers: { "Content-Type": "application/json" } },
      ),
    );

    const out = await fetchPlayerFamilySlots();
    expect(fetchMock).toHaveBeenCalledWith("/api/registry/model/player/slots");
    expect(out.family).toBe("player");
    expect(out.version_ids).toEqual(["player_slime_blue_00", ""]);
  });

  it("PUT player slots sends version_ids and returns server payload", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(
        JSON.stringify({
          family: "player",
          version_ids: ["player_slime_blue_00"],
          resolved_paths: ["player_exports/player_slime_blue_00.glb"],
        }),
        { status: 200, headers: { "Content-Type": "application/json" } },
      ),
    );

    const out = await putPlayerFamilySlots(["player_slime_blue_00"]);
    expect(fetchMock).toHaveBeenCalledWith("/api/registry/model/player/slots", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ version_ids: ["player_slime_blue_00"] }),
    });
    expect(out.resolved_paths).toEqual(["player_exports/player_slime_blue_00.glb"]);
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
              version_id: "blobert_blue_00",
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
        version_id: "blobert_blue_00",
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

  it("POST load-existing open accepts player version_id identity", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(
        JSON.stringify({
          kind: "player",
          version_id: "blobert_blue_00",
          path: "player_exports/blobert_blue_00.glb",
        }),
        { status: 200, headers: { "Content-Type": "application/json" } },
      ),
    );

    const out = await openExistingRegistryModel({
      kind: "player",
      version_id: "blobert_blue_00",
    });
    expect(fetchMock).toHaveBeenCalledWith("/api/registry/model/load_existing/open", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        kind: "player",
        version_id: "blobert_blue_00",
      }),
    });
    expect(out.path).toBe("player_exports/blobert_blue_00.glb");
    expect(out.kind).toBe("player");
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

  it("DELETE enemy version sends explicit confirmation payload", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(
        JSON.stringify({
          schema_version: 1,
          enemies: {
            spider: {
              versions: [
                { id: "spider_live_00", path: "animated_exports/spider_live_00.glb", draft: false, in_use: true },
              ],
            },
          },
          player_active_visual: { path: "player_exports/blobert_blue_00.glb", draft: false },
        }),
        { status: 200, headers: { "Content-Type": "application/json" } },
      ),
    );

    await deleteRegistryEnemyVersion("spider", "spider_draft_00", {
      delete_files: true,
      confirm: true,
      confirm_text: "delete draft spider spider_draft_00",
    });

    expect(fetchMock).toHaveBeenCalledWith("/api/registry/model/enemies/spider/versions/spider_draft_00", {
      method: "DELETE",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        delete_files: true,
        confirm: true,
        confirm_text: "delete draft spider spider_draft_00",
      }),
    });
  });

  it("DELETE player active visual sends explicit confirmation payload", async () => {
    const fetchMock = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify({ detail: "cannot delete sole active player visual" }), {
        status: 409,
        headers: { "Content-Type": "application/json" },
      }),
    );

    await expect(deleteRegistryPlayerActiveVisual({ confirm: true })).rejects.toThrow();
    expect(fetchMock).toHaveBeenCalledWith("/api/registry/model/player_active_visual", {
      method: "DELETE",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ confirm: true }),
    });
  });
});
