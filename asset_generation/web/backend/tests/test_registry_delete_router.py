"""
Primary behavioral contract tests for registry delete flows.

Spec traceability:
  DDIM-F1.1, DDIM-F1.2, DDIM-F1.3, DDIM-F1.4
  DDIM-F2.1, DDIM-F2.2, DDIM-F2.3, DDIM-F2.5
  DDIM-F3.1, DDIM-F3.2
  DDIM-NF1.1, DDIM-NF1.2, DDIM-NF1.5
"""

from __future__ import annotations

import asyncio
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
        "animated_exports/slug_live_00.glb",
        "player_exports/blobert_blue_00.glb",
    ):
        (root / rel).write_bytes(b"\x00" * 8)

    _seed_manifest(root)
    monkeypatch.setattr(config_module.settings, "python_root", root)
    return root


@pytest_asyncio.fixture()
async def client(python_root: pathlib.Path):  # noqa: ARG001
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


class TestDeleteDraftContracts:
    @pytest.mark.asyncio
    async def test_delete_draft_removes_exact_registry_row_and_target_file(
        self,
        client: AsyncClient,
        python_root: pathlib.Path,
    ) -> None:
        target_path = python_root / "animated_exports" / "spider_draft_00.glb"
        assert target_path.exists()

        res = await client.request(
            "DELETE",
            "/api/registry/model/enemies/spider/versions/spider_draft_00",
            json={"delete_files": True, "confirm": True},
        )
        assert res.status_code == 200

        manifest = json.loads((python_root / "model_registry.json").read_text(encoding="utf-8"))
        ids = [row["id"] for row in manifest["enemies"]["spider"]["versions"]]
        assert "spider_draft_00" not in ids
        assert set(ids) == {"spider_live_00", "spider_live_01"}
        assert not target_path.exists()

    @pytest.mark.asyncio
    async def test_delete_draft_rejects_non_draft_without_side_effects(
        self,
        client: AsyncClient,
        python_root: pathlib.Path,
    ) -> None:
        manifest_before = (python_root / "model_registry.json").read_text(encoding="utf-8")

        res = await client.request(
            "DELETE",
            "/api/registry/model/enemies/spider/versions/spider_live_00",
            json={"delete_files": True, "confirm": True},
        )
        assert res.status_code == 400

        manifest_after = (python_root / "model_registry.json").read_text(encoding="utf-8")
        assert manifest_after == manifest_before
        assert (python_root / "animated_exports" / "spider_live_00.glb").exists()

    @pytest.mark.asyncio
    async def test_repeat_delete_of_same_draft_returns_stale_target_without_extra_side_effects(
        self,
        client: AsyncClient,
    ) -> None:
        first = await client.request(
            "DELETE",
            "/api/registry/model/enemies/spider/versions/spider_draft_00",
            json={"delete_files": True, "confirm": True},
        )
        assert first.status_code == 200

        second = await client.request(
            "DELETE",
            "/api/registry/model/enemies/spider/versions/spider_draft_00",
            json={"delete_files": True, "confirm": True},
        )
        assert second.status_code == 404


class TestDeleteInUseContracts:
    @pytest.mark.asyncio
    async def test_delete_non_sole_in_use_version_succeeds_and_keeps_family_valid(
        self,
        client: AsyncClient,
        python_root: pathlib.Path,
    ) -> None:
        res = await client.request(
            "DELETE",
            "/api/registry/model/enemies/spider/versions/spider_live_01",
            json={
                "delete_files": True,
                "confirm": True,
                "confirm_text": "delete in-use spider spider_live_01",
            },
        )
        assert res.status_code == 200

        manifest = json.loads((python_root / "model_registry.json").read_text(encoding="utf-8"))
        versions = manifest["enemies"]["spider"]["versions"]
        ids = [row["id"] for row in versions]
        assert "spider_live_01" not in ids

        in_use_non_draft = [row for row in versions if row["in_use"] and not row["draft"]]
        assert len(in_use_non_draft) >= 1
        assert "spider_live_01" not in manifest["enemies"]["spider"]["slots"]

    @pytest.mark.asyncio
    async def test_delete_sole_in_use_enemy_version_is_blocked_without_mutation(
        self,
        client: AsyncClient,
        python_root: pathlib.Path,
    ) -> None:
        before = (python_root / "model_registry.json").read_text(encoding="utf-8")

        res = await client.request(
            "DELETE",
            "/api/registry/model/enemies/slug/versions/slug_live_00",
            json={
                "delete_files": True,
                "confirm": True,
                "confirm_text": "delete in-use slug slug_live_00",
            },
        )
        assert res.status_code == 409

        after = (python_root / "model_registry.json").read_text(encoding="utf-8")
        assert after == before
        assert (python_root / "animated_exports" / "slug_live_00.glb").exists()

    @pytest.mark.asyncio
    async def test_delete_player_active_visual_is_blocked_when_only_active_path(
        self,
        client: AsyncClient,
        python_root: pathlib.Path,
    ) -> None:
        before = (python_root / "model_registry.json").read_text(encoding="utf-8")

        res = await client.request(
            "DELETE",
            "/api/registry/model/player_active_visual",
            json={"confirm": True},
        )
        assert res.status_code == 409

        after = (python_root / "model_registry.json").read_text(encoding="utf-8")
        assert after == before


class TestDeleteErrorSurfaceContracts:
    @pytest.mark.asyncio
    async def test_delete_requires_explicit_confirmation_for_destructive_paths(
        self,
        client: AsyncClient,
    ) -> None:
        # CHECKPOINT: strictest defensible assumption is hard reject (400) when explicit confirm intent is missing.
        res = await client.request(
            "DELETE",
            "/api/registry/model/enemies/spider/versions/spider_draft_00",
            json={"delete_files": True},
        )
        assert res.status_code == 400

    @pytest.mark.asyncio
    async def test_delete_rejects_forbidden_path_class_with_403(
        self,
        client: AsyncClient,
    ) -> None:
        # CHECKPOINT: strictest defensible assumption is API-level path-class rejection before any mutation.
        res = await client.request(
            "DELETE",
            "/api/registry/model/enemies/spider/versions/spider_draft_00",
            json={
                "delete_files": True,
                "confirm": True,
                "target_path": "/tmp/escape.glb",
            },
        )
        assert res.status_code == 403

    @pytest.mark.asyncio
    async def test_error_payload_does_not_leak_absolute_paths(
        self,
        client: AsyncClient,
        python_root: pathlib.Path,
    ) -> None:
        res = await client.request(
            "DELETE",
            "/api/registry/model/enemies/slug/versions/slug_live_00",
            json={
                "delete_files": True,
                "confirm": True,
                "confirm_text": "delete in-use slug slug_live_00",
            },
        )
        assert res.status_code == 409
        detail = str(res.json().get("detail", ""))
        assert detail.strip() != ""
        assert str(python_root) not in detail


class TestDeleteAdversarialContracts:
    @pytest.mark.asyncio
    async def test_concurrent_double_delete_same_draft_is_single_success_single_stale(
        self,
        client: AsyncClient,
        python_root: pathlib.Path,
    ) -> None:
        async def _delete_once():
            return await client.request(
                "DELETE",
                "/api/registry/model/enemies/spider/versions/spider_draft_00",
                json={"delete_files": True, "confirm": True},
            )

        first, second = await asyncio.gather(_delete_once(), _delete_once())
        observed = sorted((first.status_code, second.status_code))
        assert observed == [200, 404]

        manifest = json.loads((python_root / "model_registry.json").read_text(encoding="utf-8"))
        ids = [row["id"] for row in manifest["enemies"]["spider"]["versions"]]
        assert ids.count("spider_draft_00") == 0
        assert (python_root / "animated_exports" / "spider_draft_00.glb").exists() is False

    @pytest.mark.asyncio
    async def test_in_use_delete_rejects_malformed_confirmation_text_without_write(
        self,
        client: AsyncClient,
        python_root: pathlib.Path,
    ) -> None:
        before = (python_root / "model_registry.json").read_text(encoding="utf-8")

        # CHECKPOINT: conservative assumption is malformed confirm text must hard-fail.
        res = await client.request(
            "DELETE",
            "/api/registry/model/enemies/spider/versions/spider_live_01",
            json={
                "delete_files": True,
                "confirm": True,
                "confirm_text": "delete in-use spider wrong_version",
            },
        )
        assert res.status_code == 400

        after = (python_root / "model_registry.json").read_text(encoding="utf-8")
        assert after == before
        assert (python_root / "animated_exports" / "spider_live_01.glb").exists()

    @pytest.mark.asyncio
    async def test_delete_rejects_encoded_traversal_target_path_without_mutation(
        self,
        client: AsyncClient,
        python_root: pathlib.Path,
    ) -> None:
        before = (python_root / "model_registry.json").read_text(encoding="utf-8")

        res = await client.request(
            "DELETE",
            "/api/registry/model/enemies/spider/versions/spider_draft_00",
            json={
                "delete_files": True,
                "confirm": True,
                "target_path": "animated_exports/%2e%2e/escape.glb",
            },
        )
        assert res.status_code == 400

        after = (python_root / "model_registry.json").read_text(encoding="utf-8")
        assert after == before
        assert (python_root / "animated_exports" / "spider_draft_00.glb").exists()
