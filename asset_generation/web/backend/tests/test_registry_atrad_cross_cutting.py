"""
Cross-cutting behavioral contract tests for ATRAD registry coverage.

Spec traceability:
  ATRAD-F1.1, ATRAD-F1.2, ATRAD-F1.3
  ATRAD-F2.1, ATRAD-F2.2, ATRAD-F2.3
  ATRAD-F3.1, ATRAD-F3.2, ATRAD-F3.3
  ATRAD-F4.1, ATRAD-F4.2, ATRAD-F4.3, ATRAD-F4.4
  ATRAD-NF1.1, ATRAD-NF1.2
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
                "slots": ["spider_live_00", "spider_live_01"],
                "versions": [
                    {
                        "id": "spider_live_00",
                        "path": "animated_exports/spider_live_00.glb",
                        "draft": False,
                        "in_use": True,
                    },
                    {
                        "id": "spider_live_01",
                        "path": "animated_exports/spider_live_01.glb",
                        "draft": False,
                        "in_use": True,
                    },
                    {
                        "id": "spider_draft_00",
                        "path": "animated_exports/spider_draft_00.glb",
                        "draft": True,
                        "in_use": False,
                    },
                    {
                        "id": "spider_draft_marked_in_use",
                        "path": "animated_exports/spider_draft_marked_in_use.glb",
                        "draft": True,
                        "in_use": True,
                    },
                ],
            },
            "slug": {
                "slots": ["slug_live_00"],
                "versions": [
                    {
                        "id": "slug_live_00",
                        "path": "animated_exports/slug_live_00.glb",
                        "draft": False,
                        "in_use": True,
                    },
                ],
            },
            "wisp": {
                "slots": [],
                "versions": [
                    {
                        "id": "wisp_draft_00",
                        "path": "animated_exports/wisp_draft_00.glb",
                        "draft": True,
                        "in_use": False,
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
    (root / "animated_exports").mkdir(parents=True)
    (root / "player_exports").mkdir(parents=True)

    for rel in (
        "animated_exports/spider_live_00.glb",
        "animated_exports/spider_live_01.glb",
        "animated_exports/spider_draft_00.glb",
        "animated_exports/spider_draft_marked_in_use.glb",
        "animated_exports/slug_live_00.glb",
        "animated_exports/wisp_draft_00.glb",
        "player_exports/blobert_blue_00.glb",
        "player_exports/blobert_green_00.glb",
    ):
        (root / rel).write_bytes(b"\x00" * 8)

    _seed_manifest(root)
    monkeypatch.setattr(config_module.settings, "python_root", root)
    return root


@pytest_asyncio.fixture()
async def client(python_root: pathlib.Path):  # noqa: ARG001
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


def _read_manifest(python_root: pathlib.Path) -> dict[str, object]:
    return json.loads((python_root / "model_registry.json").read_text(encoding="utf-8"))


class TestAtradF1RegistryReadWrite:
    @pytest.mark.asyncio
    async def test_atrad_f1_1_write_then_read_reflects_persisted_player_active_visual(
        self,
        client: AsyncClient,
        python_root: pathlib.Path,
    ) -> None:
        update = await client.patch(
            "/api/registry/model/player_active_visual",
            json={"path": "player_exports/blobert_green_00.glb"},
        )
        assert update.status_code == 200

        reread = await client.get("/api/registry/model")
        assert reread.status_code == 200
        assert reread.json()["player_active_visual"] == {
            "path": "player_exports/blobert_green_00.glb",
            "draft": False,
        }

        persisted = _read_manifest(python_root)
        assert persisted["player_active_visual"] == {
            "path": "player_exports/blobert_green_00.glb",
            "draft": False,
        }

    @pytest.mark.asyncio
    async def test_atrad_f1_2_invalid_mutation_rejected_without_manifest_change(
        self,
        client: AsyncClient,
        python_root: pathlib.Path,
    ) -> None:
        before = (python_root / "model_registry.json").read_text(encoding="utf-8")

        rejected = await client.patch(
            "/api/registry/model/player_active_visual",
            json={"path": "outside/not_allowlisted.glb"},
        )
        assert rejected.status_code == 400

        after = (python_root / "model_registry.json").read_text(encoding="utf-8")
        assert after == before


class TestAtradF2AllowlistAndPathRejection:
    @pytest.mark.asyncio
    async def test_atrad_f2_1_outside_allowlist_path_rejected_with_no_state_mutation(
        self,
        client: AsyncClient,
        python_root: pathlib.Path,
    ) -> None:
        before = (python_root / "model_registry.json").read_text(encoding="utf-8")

        res = await client.post(
            "/api/registry/model/load_existing/open",
            json={"kind": "path", "path": "outside/not_allowlisted.glb"},
        )
        assert res.status_code == 403

        after = (python_root / "model_registry.json").read_text(encoding="utf-8")
        assert after == before

    @pytest.mark.asyncio
    async def test_atrad_f2_2_traversal_vector_rejected_with_deterministic_failure_class(
        self,
        client: AsyncClient,
    ) -> None:
        payload = {"kind": "path", "path": "../animated_exports/spider_live_00.glb"}

        first = await client.post("/api/registry/model/load_existing/open", json=payload)
        second = await client.post("/api/registry/model/load_existing/open", json=payload)
        assert first.status_code == 400
        assert second.status_code == 400

    @pytest.mark.asyncio
    async def test_atrad_f2_3_rejection_payload_is_non_leaky(
        self,
        client: AsyncClient,
        python_root: pathlib.Path,
    ) -> None:
        res = await client.post(
            "/api/registry/model/load_existing/open",
            json={"kind": "path", "path": "../animated_exports/spider_live_00.glb"},
        )
        assert res.status_code == 400
        detail = str(res.json().get("detail", ""))
        lowered = detail.lower()

        assert str(python_root) not in detail
        assert "traceback" not in lowered
        assert "/users/" not in lowered

    @pytest.mark.asyncio
    async def test_adv_atrad_f2_encoded_traversal_and_malformed_encoding_rejected(
        self,
        client: AsyncClient,
    ) -> None:
        encoded_traversal = {"kind": "path", "path": "%2e%2e/animated_exports/spider_live_00.glb"}
        malformed_encoding = {"kind": "path", "path": "animated_exports/%zz.glb"}

        traversal_res = await client.post("/api/registry/model/load_existing/open", json=encoded_traversal)
        malformed_res = await client.post("/api/registry/model/load_existing/open", json=malformed_encoding)

        assert traversal_res.status_code == 400
        assert malformed_res.status_code == 400

    @pytest.mark.asyncio
    async def test_adv_atrad_f2_mixed_identity_and_path_payload_is_rejected(
        self,
        client: AsyncClient,
        python_root: pathlib.Path,
    ) -> None:
        before = (python_root / "model_registry.json").read_text(encoding="utf-8")
        payload = {
            "kind": "path",
            "path": "animated_exports/spider_live_00.glb",
            "family": "spider",
            "version_id": "spider_live_00",
        }
        res = await client.post("/api/registry/model/load_existing/open", json=payload)
        assert res.status_code == 400

        after = (python_root / "model_registry.json").read_text(encoding="utf-8")
        assert after == before


class TestAtradF3DraftExclusionFromDefaultReader:
    @pytest.mark.asyncio
    async def test_atrad_f3_1_default_spawn_eligible_returns_only_non_draft_in_use(
        self,
        client: AsyncClient,
    ) -> None:
        res = await client.get("/api/registry/model/spawn_eligible/spider")
        assert res.status_code == 200
        body = res.json()
        assert body["family"] == "spider"
        assert body["paths"] == [
            "animated_exports/spider_live_00.glb",
            "animated_exports/spider_live_01.glb",
        ]

    @pytest.mark.asyncio
    async def test_atrad_f3_2_only_draft_family_returns_empty_default_spawn_pool(
        self,
        client: AsyncClient,
    ) -> None:
        res = await client.get("/api/registry/model/spawn_eligible/wisp")
        assert res.status_code == 200
        assert res.json()["paths"] == []

    @pytest.mark.asyncio
    async def test_atrad_f3_3_draft_flag_wins_over_in_use_for_default_reader(
        self,
        client: AsyncClient,
    ) -> None:
        res = await client.get("/api/registry/model/spawn_eligible/spider")
        assert res.status_code == 200
        paths = res.json()["paths"]
        assert "animated_exports/spider_draft_marked_in_use.glb" not in paths


class TestAtradF4DeleteInvariants:
    @pytest.mark.asyncio
    async def test_atrad_f4_1_blocked_sole_in_use_delete_leaves_state_unchanged(
        self,
        client: AsyncClient,
        python_root: pathlib.Path,
    ) -> None:
        before = (python_root / "model_registry.json").read_text(encoding="utf-8")

        blocked = await client.request(
            "DELETE",
            "/api/registry/model/enemies/slug/versions/slug_live_00",
            json={
                "confirm": True,
                "delete_files": True,
                "confirm_text": "delete in-use slug slug_live_00",
            },
        )
        assert blocked.status_code == 409

        after = (python_root / "model_registry.json").read_text(encoding="utf-8")
        assert after == before
        assert (python_root / "animated_exports" / "slug_live_00.glb").exists()

    @pytest.mark.asyncio
    async def test_atrad_f4_2_and_f4_3_allowed_delete_removes_references_and_reads_consistent(
        self,
        client: AsyncClient,
        python_root: pathlib.Path,
    ) -> None:
        allowed = await client.request(
            "DELETE",
            "/api/registry/model/enemies/spider/versions/spider_live_01",
            json={
                "confirm": True,
                "delete_files": True,
                "confirm_text": "delete in-use spider spider_live_01",
            },
        )
        assert allowed.status_code == 200

        manifest = _read_manifest(python_root)
        spider = manifest["enemies"]["spider"]
        version_ids = [row["id"] for row in spider["versions"]]
        assert "spider_live_01" not in version_ids
        assert "spider_live_01" not in spider.get("slots", [])

        spawn_read = await client.get("/api/registry/model/spawn_eligible/spider")
        assert spawn_read.status_code == 200
        assert "animated_exports/spider_live_01.glb" not in spawn_read.json()["paths"]

    @pytest.mark.asyncio
    async def test_atrad_f4_4_repeat_delete_of_stale_target_is_deterministic_not_found(
        self,
        client: AsyncClient,
    ) -> None:
        first = await client.request(
            "DELETE",
            "/api/registry/model/enemies/spider/versions/spider_draft_00",
            json={"confirm": True, "delete_files": True},
        )
        assert first.status_code == 200

        second = await client.request(
            "DELETE",
            "/api/registry/model/enemies/spider/versions/spider_draft_00",
            json={"confirm": True, "delete_files": True},
        )
        assert second.status_code == 404

    @pytest.mark.asyncio
    async def test_adv_atrad_f4_delete_target_path_mismatch_rejected_without_side_effects(
        self,
        client: AsyncClient,
        python_root: pathlib.Path,
    ) -> None:
        before = (python_root / "model_registry.json").read_text(encoding="utf-8")

        blocked = await client.request(
            "DELETE",
            "/api/registry/model/enemies/spider/versions/spider_draft_00",
            json={
                "confirm": True,
                "delete_files": True,
                "target_path": "animated_exports/slug_live_00.glb",
            },
        )
        assert blocked.status_code == 403

        after = (python_root / "model_registry.json").read_text(encoding="utf-8")
        assert after == before
        assert (python_root / "animated_exports" / "spider_draft_00.glb").exists()

    @pytest.mark.asyncio
    async def test_adv_atrad_f4_in_use_delete_requires_exact_confirmation_text(
        self,
        client: AsyncClient,
        python_root: pathlib.Path,
    ) -> None:
        before = (python_root / "model_registry.json").read_text(encoding="utf-8")
        res = await client.request(
            "DELETE",
            "/api/registry/model/enemies/spider/versions/spider_live_00",
            json={
                "confirm": True,
                "delete_files": True,
                "confirm_text": "delete in use spider spider_live_00",
            },
        )
        assert res.status_code == 400

        after = (python_root / "model_registry.json").read_text(encoding="utf-8")
        assert after == before
        assert (python_root / "animated_exports" / "spider_live_00.glb").exists()

    @pytest.mark.asyncio
    async def test_adv_atrad_f4_stress_repeated_invalid_delete_is_deterministic_and_atomic(
        self,
        client: AsyncClient,
        python_root: pathlib.Path,
    ) -> None:
        before = (python_root / "model_registry.json").read_text(encoding="utf-8")

        for _ in range(25):
            res = await client.request(
                "DELETE",
                "/api/registry/model/enemies/slug/versions/slug_live_00",
                json={
                    "confirm": True,
                    "delete_files": True,
                    "confirm_text": "delete in-use slug slug_live_00",
                },
            )
            assert res.status_code == 409

        after = (python_root / "model_registry.json").read_text(encoding="utf-8")
        assert after == before
        assert (python_root / "animated_exports" / "slug_live_00.glb").exists()

    @pytest.mark.asyncio
    async def test_adv_atrad_f4_draft_delete_rejects_blank_confirmation_text_checkpoint(
        self,
        client: AsyncClient,
        python_root: pathlib.Path,
    ) -> None:
        # CHECKPOINT: conservative assumption is that explicit blank confirm_text should be rejected
        # when provided, rather than treated as omitted.
        before = (python_root / "model_registry.json").read_text(encoding="utf-8")
        res = await client.request(
            "DELETE",
            "/api/registry/model/enemies/spider/versions/spider_draft_00",
            json={"confirm": True, "delete_files": True, "confirm_text": "   "},
        )
        assert res.status_code == 400

        after = (python_root / "model_registry.json").read_text(encoding="utf-8")
        assert after == before
