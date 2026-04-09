"""
Behavioral contract tests for EGMS player model selection + enemy slot endpoints.

Spec traceability:
  EGMS-1.1, EGMS-1.2, EGMS-1.3
  EGMS-2.1, EGMS-2.2, EGMS-2.3, EGMS-2.4
  EGMS-3.1 (read-after-restart persistence check)
"""

from __future__ import annotations

import json
import pathlib

import core.config as config_module
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from main import app


def _seed_manifest(python_root: pathlib.Path) -> None:
    payload = {
        "schema_version": 1,
        "enemies": {
            "spider": {
                "versions": [
                    {
                        "id": "spider_animated_00",
                        "path": "animated_exports/spider_animated_00.glb",
                        "draft": False,
                        "in_use": True,
                    },
                    {
                        "id": "spider_animated_01",
                        "path": "animated_exports/spider_animated_01.glb",
                        "draft": False,
                        "in_use": True,
                    },
                    {
                        "id": "spider_animated_draft",
                        "path": "animated_exports/spider_animated_draft.glb",
                        "draft": True,
                        "in_use": False,
                    },
                ],
            },
            "slug": {
                "versions": [
                    {
                        "id": "slug_animated_00",
                        "path": "animated_exports/slug_animated_00.glb",
                        "draft": False,
                        "in_use": True,
                    },
                ],
            },
        },
        "player_active_visual": {
            "path": "player_exports/blobert_blue_00.glb",
            "draft": False,
        },
    }
    (python_root / "model_registry.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


@pytest.fixture()
def python_root(tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> pathlib.Path:
    root = tmp_path / "python"
    root.mkdir(parents=True)
    _seed_manifest(root)
    monkeypatch.setattr(config_module.settings, "python_root", root)
    return root


@pytest_asyncio.fixture()
async def client(python_root: pathlib.Path):  # noqa: ARG001
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


class TestPlayerActiveVisualSelection:
    @pytest.mark.asyncio
    async def test_select_valid_player_model_persists_non_draft(
        self,
        client: AsyncClient,
        python_root: pathlib.Path,
    ) -> None:
        res = await client.patch(
            "/api/registry/model/player_active_visual",
            json={"path": "player_exports/blobert_pink_00.glb"},
        )
        assert res.status_code == 200
        body = res.json()
        assert body["player_active_visual"]["path"] == "player_exports/blobert_pink_00.glb"
        assert body["player_active_visual"]["draft"] is False

        persisted = json.loads((python_root / "model_registry.json").read_text(encoding="utf-8"))
        assert persisted["player_active_visual"]["path"] == "player_exports/blobert_pink_00.glb"
        assert persisted["player_active_visual"]["draft"] is False

    @pytest.mark.asyncio
    async def test_select_new_player_model_replaces_prior_active_path(
        self,
        client: AsyncClient,
    ) -> None:
        first = await client.patch(
            "/api/registry/model/player_active_visual",
            json={"path": "player_exports/blobert_pink_00.glb"},
        )
        assert first.status_code == 200
        second = await client.patch(
            "/api/registry/model/player_active_visual",
            json={"path": "player_exports/blobert_green_00.glb"},
        )
        assert second.status_code == 200
        assert second.json()["player_active_visual"] == {
            "path": "player_exports/blobert_green_00.glb",
            "draft": False,
        }

    @pytest.mark.asyncio
    async def test_rejects_disallowed_path_and_keeps_existing_player_visual(
        self,
        client: AsyncClient,
        python_root: pathlib.Path,
    ) -> None:
        before = json.loads((python_root / "model_registry.json").read_text(encoding="utf-8"))
        res = await client.patch(
            "/api/registry/model/player_active_visual",
            json={"path": "outside/blobert.glb"},
        )
        assert res.status_code == 400

        after = json.loads((python_root / "model_registry.json").read_text(encoding="utf-8"))
        assert after["player_active_visual"] == before["player_active_visual"]

    @pytest.mark.asyncio
    async def test_rejects_draft_true_for_active_player_visual(
        self,
        client: AsyncClient,
        python_root: pathlib.Path,
    ) -> None:
        before = json.loads((python_root / "model_registry.json").read_text(encoding="utf-8"))
        res = await client.patch(
            "/api/registry/model/player_active_visual",
            json={"draft": True},
        )
        assert res.status_code == 400

        after = json.loads((python_root / "model_registry.json").read_text(encoding="utf-8"))
        assert after["player_active_visual"] == before["player_active_visual"]

    @pytest.mark.asyncio
    async def test_persists_across_reload_after_player_visual_change(
        self,
        client: AsyncClient,
    ) -> None:
        patch_res = await client.patch(
            "/api/registry/model/player_active_visual",
            json={"path": "player_exports/blobert_yellow_00.glb"},
        )
        assert patch_res.status_code == 200

        get_res = await client.get("/api/registry/model")
        assert get_res.status_code == 200
        assert get_res.json()["player_active_visual"] == {
            "path": "player_exports/blobert_yellow_00.glb",
            "draft": False,
        }


class TestEnemySlotManagement:
    @pytest.mark.asyncio
    async def test_put_slots_persists_order_and_resolved_paths(
        self,
        client: AsyncClient,
    ) -> None:
        res = await client.put(
            "/api/registry/model/enemies/spider/slots",
            json={"version_ids": ["spider_animated_01", "spider_animated_00"]},
        )
        assert res.status_code == 200
        body = res.json()
        assert body["family"] == "spider"
        assert body["version_ids"] == ["spider_animated_01", "spider_animated_00"]
        assert body["resolved_paths"] == [
            "animated_exports/spider_animated_01.glb",
            "animated_exports/spider_animated_00.glb",
        ]

    @pytest.mark.asyncio
    async def test_put_slots_rejects_draft_version_without_partial_write(
        self,
        client: AsyncClient,
    ) -> None:
        seed = await client.put(
            "/api/registry/model/enemies/spider/slots",
            json={"version_ids": ["spider_animated_00"]},
        )
        assert seed.status_code == 200

        bad = await client.put(
            "/api/registry/model/enemies/spider/slots",
            json={"version_ids": ["spider_animated_00", "spider_animated_draft"]},
        )
        assert bad.status_code == 400

        reread = await client.get("/api/registry/model/enemies/spider/slots")
        assert reread.status_code == 200
        assert reread.json()["version_ids"] == ["spider_animated_00"]

    @pytest.mark.asyncio
    async def test_put_slots_rejects_duplicate_version_ids(
        self,
        client: AsyncClient,
    ) -> None:
        res = await client.put(
            "/api/registry/model/enemies/spider/slots",
            json={"version_ids": ["spider_animated_00", "spider_animated_00"]},
        )
        assert res.status_code == 400

    @pytest.mark.asyncio
    async def test_put_slots_unknown_family_or_version_returns_404(
        self,
        client: AsyncClient,
    ) -> None:
        unknown_family = await client.put(
            "/api/registry/model/enemies/not_real/slots",
            json={"version_ids": ["spider_animated_00"]},
        )
        assert unknown_family.status_code == 404

        unknown_version = await client.put(
            "/api/registry/model/enemies/spider/slots",
            json={"version_ids": ["does_not_exist"]},
        )
        assert unknown_version.status_code == 404

    @pytest.mark.asyncio
    async def test_put_slots_rejects_version_from_different_family_without_write(
        self,
        client: AsyncClient,
    ) -> None:
        seed = await client.put(
            "/api/registry/model/enemies/spider/slots",
            json={"version_ids": ["spider_animated_00"]},
        )
        assert seed.status_code == 200

        res = await client.put(
            "/api/registry/model/enemies/spider/slots",
            json={"version_ids": ["slug_animated_00"]},
        )
        assert res.status_code == 404

        reread = await client.get("/api/registry/model/enemies/spider/slots")
        assert reread.status_code == 200
        assert reread.json()["version_ids"] == ["spider_animated_00"]

    @pytest.mark.asyncio
    async def test_put_slots_rejects_non_in_use_version_without_partial_write(
        self,
        client: AsyncClient,
        python_root: pathlib.Path,
    ) -> None:
        seed = await client.put(
            "/api/registry/model/enemies/spider/slots",
            json={"version_ids": ["spider_animated_00"]},
        )
        assert seed.status_code == 200

        manifest_path = python_root / "model_registry.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        for version in manifest["enemies"]["spider"]["versions"]:
            if version["id"] == "spider_animated_01":
                version["in_use"] = False
        manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

        res = await client.put(
            "/api/registry/model/enemies/spider/slots",
            json={"version_ids": ["spider_animated_01"]},
        )
        assert res.status_code == 400

        reread = await client.get("/api/registry/model/enemies/spider/slots")
        assert reread.status_code == 200
        assert reread.json()["version_ids"] == ["spider_animated_00"]

    @pytest.mark.asyncio
    async def test_put_slots_rejects_empty_list_and_preserves_existing_state(
        self,
        client: AsyncClient,
    ) -> None:
        seed = await client.put(
            "/api/registry/model/enemies/spider/slots",
            json={"version_ids": ["spider_animated_00"]},
        )
        assert seed.status_code == 200

        res = await client.put(
            "/api/registry/model/enemies/spider/slots",
            json={"version_ids": []},
        )
        assert res.status_code == 400

        reread = await client.get("/api/registry/model/enemies/spider/slots")
        assert reread.status_code == 200
        assert reread.json()["version_ids"] == ["spider_animated_00"]

    @pytest.mark.asyncio
    async def test_put_slots_mixed_invalid_payload_has_atomic_rejection(
        self,
        client: AsyncClient,
    ) -> None:
        seed = await client.put(
            "/api/registry/model/enemies/spider/slots",
            json={"version_ids": ["spider_animated_01"]},
        )
        assert seed.status_code == 200

        # CHECKPOINT: conservative assumption is that mixed invalid payloads are rejected atomically.
        res = await client.put(
            "/api/registry/model/enemies/spider/slots",
            json={"version_ids": ["spider_animated_00", "spider_animated_00", "does_not_exist"]},
        )
        assert res.status_code in (400, 404)

        reread = await client.get("/api/registry/model/enemies/spider/slots")
        assert reread.status_code == 200
        assert reread.json()["version_ids"] == ["spider_animated_01"]

    @pytest.mark.asyncio
    async def test_put_slots_stress_large_duplicate_payload_rejected_deterministically(
        self,
        client: AsyncClient,
    ) -> None:
        seed = await client.put(
            "/api/registry/model/enemies/spider/slots",
            json={"version_ids": ["spider_animated_01"]},
        )
        assert seed.status_code == 200

        version_ids = ["spider_animated_00"] * 128
        res = await client.put(
            "/api/registry/model/enemies/spider/slots",
            json={"version_ids": version_ids},
        )
        assert res.status_code == 400

        reread = await client.get("/api/registry/model/enemies/spider/slots")
        assert reread.status_code == 200
        assert reread.json()["version_ids"] == ["spider_animated_01"]


def _seed_manifest_player_visual_null(python_root: pathlib.Path) -> None:
    payload = {
        "schema_version": 1,
        "enemies": {
            "spider": {
                "slots": ["spider_animated_00"],
                "versions": [
                    {
                        "id": "spider_animated_00",
                        "path": "animated_exports/spider_animated_00.glb",
                        "draft": False,
                        "in_use": True,
                    },
                ],
            },
        },
        "player_active_visual": None,
    }
    (python_root / "model_registry.json").write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


@pytest.fixture()
def python_root_player_visual_null(
    tmp_path: pathlib.Path,
    monkeypatch: pytest.MonkeyPatch,
) -> pathlib.Path:
    root = tmp_path / "python"
    (root / "animated_exports").mkdir(parents=True)
    (root / "player_exports").mkdir(parents=True)
    (root / "animated_exports" / "spider_animated_00.glb").write_bytes(b"\x00" * 8)
    (root / "player_exports" / "blobert_green_00.glb").write_bytes(b"\x00" * 8)
    _seed_manifest_player_visual_null(root)
    monkeypatch.setattr(config_module.settings, "python_root", root)
    return root


@pytest_asyncio.fixture()
async def client_player_visual_null(python_root_player_visual_null: pathlib.Path):  # noqa: ARG001
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


class TestPlayerActiveVisualNullInit:
    @pytest.mark.asyncio
    async def test_patch_with_path_initializes_when_player_active_visual_was_null(
        self,
        client_player_visual_null: AsyncClient,
        python_root_player_visual_null: pathlib.Path,
    ) -> None:
        res = await client_player_visual_null.patch(
            "/api/registry/model/player_active_visual",
            json={"path": "player_exports/blobert_green_00.glb"},
        )
        assert res.status_code == 200
        assert res.json()["player_active_visual"] == {
            "path": "player_exports/blobert_green_00.glb",
            "draft": False,
        }
        persisted = json.loads((python_root_player_visual_null / "model_registry.json").read_text(encoding="utf-8"))
        assert persisted["player_active_visual"] == {
            "path": "player_exports/blobert_green_00.glb",
            "draft": False,
        }

    @pytest.mark.asyncio
    async def test_patch_without_path_when_null_returns_400(
        self,
        client_player_visual_null: AsyncClient,
        python_root_player_visual_null: pathlib.Path,
    ) -> None:
        before = (python_root_player_visual_null / "model_registry.json").read_text(encoding="utf-8")
        res = await client_player_visual_null.patch(
            "/api/registry/model/player_active_visual",
            json={"draft": False},
        )
        assert res.status_code == 400
        after = (python_root_player_visual_null / "model_registry.json").read_text(encoding="utf-8")
        assert after == before

    @pytest.mark.asyncio
    async def test_patch_invalid_path_when_null_leaves_manifest_unchanged(
        self,
        client_player_visual_null: AsyncClient,
        python_root_player_visual_null: pathlib.Path,
    ) -> None:
        before = (python_root_player_visual_null / "model_registry.json").read_text(encoding="utf-8")
        res = await client_player_visual_null.patch(
            "/api/registry/model/player_active_visual",
            json={"path": "outside/not_allowlisted.glb"},
        )
        assert res.status_code == 400
        after = (python_root_player_visual_null / "model_registry.json").read_text(encoding="utf-8")
        assert after == before


class TestSyncAnimatedExports:
    @pytest.mark.asyncio
    async def test_post_adds_version_row_for_new_glb_on_disk(
        self,
        client: AsyncClient,
        python_root: pathlib.Path,
    ) -> None:
        exports = python_root / "animated_exports"
        exports.mkdir(parents=True, exist_ok=True)
        (exports / "slug_animated_01.glb").write_bytes(b"\x00" * 4)
        res = await client.post("/api/registry/model/enemies/slug/sync_animated_exports")
        assert res.status_code == 200
        body = res.json()
        ids = [v["id"] for v in body["enemies"]["slug"]["versions"]]
        assert ids == ["slug_animated_00", "slug_animated_01"]
        disk = json.loads((python_root / "model_registry.json").read_text(encoding="utf-8"))
        assert len(disk["enemies"]["slug"]["versions"]) == 2

    @pytest.mark.asyncio
    async def test_post_unknown_family_404(self, client: AsyncClient) -> None:
        res = await client.post("/api/registry/model/enemies/nonexistent_enemy_xyz/sync_animated_exports")
        assert res.status_code == 404
