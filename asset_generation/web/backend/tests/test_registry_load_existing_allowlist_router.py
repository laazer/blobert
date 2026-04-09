"""
Primary behavioral contract tests for the load/open-existing registry workflow.

Spec traceability:
  LEMA-F1.1, LEMA-F1.2, LEMA-F1.3, LEMA-F1.4
  LEMA-F2.1, LEMA-F2.2, LEMA-F2.3, LEMA-F2.4
  LEMA-F4.1, LEMA-F4.2, LEMA-F4.3
  LEMA-NF1.2, LEMA-NF1.3
"""

from __future__ import annotations

import json
import pathlib

import core.config as config_module
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from main import app

_DETERMINISM_REPEAT_COUNT = 25


def _seed_manifest(python_root: pathlib.Path) -> None:
    payload = {
        "schema_version": 1,
        "enemies": {
            "alpha": {
                "versions": [
                    {
                        "id": "alpha_draft_00",
                        "path": "animated_exports/alpha_draft_00.glb",
                        "draft": True,
                        "in_use": False,
                    },
                    {
                        "id": "alpha_live_00",
                        "path": "animated_exports/alpha_live_00.glb",
                        "draft": False,
                        "in_use": True,
                    },
                    {
                        "id": "alpha_filtered_00",
                        "path": "animated_exports/alpha_filtered_00.glb",
                        "draft": False,
                        "in_use": False,
                    },
                ],
            },
            "beta": {
                "versions": [
                    {
                        "id": "beta_live_00",
                        "path": "exports/beta_live_00.glb",
                        "draft": False,
                        "in_use": True,
                    },
                    {
                        "id": "beta_invalid_abs",
                        "path": "/tmp/escape.glb",
                        "draft": True,
                        "in_use": False,
                    },
                    {
                        "id": "beta_invalid_traversal",
                        "path": "animated_exports/../outside.glb",
                        "draft": True,
                        "in_use": False,
                    },
                    {
                        "id": "beta_invalid_prefix",
                        "path": "concept_art/not_allowed.glb",
                        "draft": True,
                        "in_use": False,
                    },
                    {
                        "id": "beta_invalid_ext",
                        "path": "exports/not_glb.txt",
                        "draft": True,
                        "in_use": False,
                    },
                    {
                        "id": "beta_invalid_encoded_traversal",
                        "path": "animated_exports/%2e%2e/escape.glb",
                        "draft": True,
                        "in_use": False,
                    },
                    {
                        "id": "beta_invalid_double_encoded_traversal",
                        "path": "animated_exports/%252e%252e/escape.glb",
                        "draft": True,
                        "in_use": False,
                    },
                    {
                        "id": "beta_invalid_upper_ext",
                        "path": "exports/not_lowercase.GLB",
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
    root.mkdir(parents=True)

    # On-disk extras that must never leak into candidate responses.
    animated = root / "animated_exports"
    animated.mkdir(parents=True)
    (animated / "orphan_disk_only.glb").write_bytes(b"\x00" * 8)
    (animated / "alpha_live_00.glb").write_bytes(b"\x00" * 8)

    exports = root / "exports"
    exports.mkdir(parents=True)
    (exports / "beta_live_00.glb").write_bytes(b"\x00" * 8)

    player_exports = root / "player_exports"
    player_exports.mkdir(parents=True)
    (player_exports / "blobert_blue_00.glb").write_bytes(b"\x00" * 8)

    _seed_manifest(root)
    monkeypatch.setattr(config_module.settings, "python_root", root)
    return root


@pytest_asyncio.fixture()
async def client(python_root: pathlib.Path):  # noqa: ARG001
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


class TestLoadExistingCandidates:
    @pytest.mark.asyncio
    async def test_candidates_include_only_draft_or_in_use_registry_rows(
        self,
        client: AsyncClient,
    ) -> None:
        res = await client.get("/api/registry/model/load_existing/candidates")
        assert res.status_code == 200
        rows = res.json()["candidates"]

        # LEMA-F1.1 + LEMA-F1.3: only registry-backed draft or in-use records survive.
        ids = {(row.get("family"), row.get("version_id")) for row in rows if row.get("kind") == "enemy"}
        assert ("alpha", "alpha_draft_00") in ids
        assert ("alpha", "alpha_live_00") in ids
        assert ("alpha", "alpha_filtered_00") not in ids
        assert ("beta", "beta_live_00") in ids

        player_rows = [row for row in rows if row.get("kind") == "player"]
        assert len(player_rows) == 1
        assert player_rows[0]["version_id"] == "blobert_blue_00"
        assert player_rows[0]["path"] == "player_exports/blobert_blue_00.glb"

    @pytest.mark.asyncio
    async def test_candidates_exclude_invalid_or_out_of_allowlist_paths(
        self,
        client: AsyncClient,
    ) -> None:
        res = await client.get("/api/registry/model/load_existing/candidates")
        assert res.status_code == 200
        rows = res.json()["candidates"]
        paths = {row["path"] for row in rows}

        # LEMA-F1.2: no absolute, traversal, disallowed roots, or non-.glb.
        assert "/tmp/escape.glb" not in paths
        assert "animated_exports/../outside.glb" not in paths
        assert "concept_art/not_allowed.glb" not in paths
        assert "exports/not_glb.txt" not in paths
        assert "animated_exports/%2e%2e/escape.glb" not in paths
        assert "animated_exports/%252e%252e/escape.glb" not in paths
        assert "exports/not_lowercase.GLB" not in paths

    @pytest.mark.asyncio
    async def test_candidates_are_deterministically_sorted_for_fixed_manifest(
        self,
        client: AsyncClient,
    ) -> None:
        first = await client.get("/api/registry/model/load_existing/candidates")
        second = await client.get("/api/registry/model/load_existing/candidates")
        assert first.status_code == 200
        assert second.status_code == 200

        # LEMA-F1.4 + LEMA-NF1.2: deterministic, stable shape/order.
        assert first.json()["candidates"] == second.json()["candidates"]

        rows = first.json()["candidates"]
        enemy_rows = [r for r in rows if r.get("kind") == "enemy"]
        enemy_order = [(r["family"], r["version_id"]) for r in enemy_rows]
        assert enemy_order == sorted(enemy_order)

    @pytest.mark.asyncio
    async def test_candidates_do_not_include_disk_only_glbs_absent_from_registry(
        self,
        client: AsyncClient,
    ) -> None:
        res = await client.get("/api/registry/model/load_existing/candidates")
        assert res.status_code == 200
        paths = {row["path"] for row in res.json()["candidates"]}

        # LEMA-F1.3: raw files are never candidates without registry backing.
        assert "animated_exports/orphan_disk_only.glb" not in paths


class TestLoadExistingOpenEndpoint:
    @pytest.mark.asyncio
    async def test_open_valid_registry_identity_returns_resolved_canonical_path(
        self,
        client: AsyncClient,
    ) -> None:
        res = await client.post(
            "/api/registry/model/load_existing/open",
            json={"kind": "enemy", "family": "alpha", "version_id": "alpha_live_00"},
        )
        assert res.status_code == 200
        body = res.json()
        assert body["path"] == "animated_exports/alpha_live_00.glb"
        assert body["kind"] == "enemy"
        assert body["family"] == "alpha"
        assert body["version_id"] == "alpha_live_00"

    @pytest.mark.asyncio
    async def test_open_valid_player_identity_returns_resolved_canonical_path(
        self,
        client: AsyncClient,
    ) -> None:
        res = await client.post(
            "/api/registry/model/load_existing/open",
            json={"kind": "player", "version_id": "blobert_blue_00"},
        )
        assert res.status_code == 200
        body = res.json()
        assert body["path"] == "player_exports/blobert_blue_00.glb"
        assert body["kind"] == "player"
        assert body["version_id"] == "blobert_blue_00"

    @pytest.mark.asyncio
    async def test_open_rejects_traversal_like_payloads_with_400_or_403(
        self,
        client: AsyncClient,
    ) -> None:
        vectors = [
            {"kind": "path", "path": "../animated_exports/alpha_live_00.glb"},
            {"kind": "path", "path": "%2e%2e/animated_exports/alpha_live_00.glb"},
            {"kind": "path", "path": r"..\\animated_exports\\alpha_live_00.glb"},
            {"kind": "path", "path": "animated_exports/%2e%2e/alpha_live_00.glb"},
        ]
        for payload in vectors:
            res = await client.post("/api/registry/model/load_existing/open", json=payload)
            # LEMA-F2.2 + LEMA-F4.1: malformed(400) or forbidden(403), never success.
            assert res.status_code in (400, 403)
            detail = str(res.json().get("detail", ""))
            assert detail.strip() != ""

    @pytest.mark.asyncio
    async def test_open_rejects_raw_arbitrary_absolute_or_res_paths(
        self,
        client: AsyncClient,
    ) -> None:
        attempts = [
            {"kind": "path", "path": "/abs/path.glb"},
            {"kind": "path", "path": "res://asset_generation/python/animated_exports/a.glb"},
            {"kind": "path", "path": "concept_art/freeform.glb"},
        ]
        for payload in attempts:
            res = await client.post("/api/registry/model/load_existing/open", json=payload)
            assert res.status_code in (400, 403)
            detail = str(res.json().get("detail", ""))
            assert detail.strip() != ""

    @pytest.mark.asyncio
    async def test_open_rejects_double_encoded_and_control_character_vectors(
        self,
        client: AsyncClient,
    ) -> None:
        vectors = [
            {"kind": "path", "path": "animated_exports/%252e%252e/alpha_live_00.glb"},
            {"kind": "path", "path": "animated_exports/alpha_live_00.glb%00.png"},
            {"kind": "path", "path": "animated_exports/\nalpha_live_00.glb"},
            {"kind": "path", "path": "animated_exports/\ralpha_live_00.glb"},
        ]
        for payload in vectors:
            res = await client.post("/api/registry/model/load_existing/open", json=payload)
            assert res.status_code in (400, 403)
            detail = str(res.json().get("detail", ""))
            assert detail.strip() != ""

    @pytest.mark.asyncio
    async def test_open_rejects_ambiguous_identity_plus_path_payload(
        self,
        client: AsyncClient,
    ) -> None:
        # CHECKPOINT: Conservative contract assumption for mixed identity+path payloads is hard reject (400), never permissive fallback.
        res = await client.post(
            "/api/registry/model/load_existing/open",
            json={
                "kind": "enemy",
                "family": "alpha",
                "version_id": "alpha_live_00",
                "path": "/tmp/escape.glb",
            },
        )
        assert res.status_code == 400
        detail = str(res.json().get("detail", ""))
        assert detail.strip() != ""

    @pytest.mark.asyncio
    async def test_open_rejection_detail_does_not_leak_host_python_root(
        self,
        client: AsyncClient,
        python_root: pathlib.Path,
    ) -> None:
        res = await client.post(
            "/api/registry/model/load_existing/open",
            json={"kind": "path", "path": "/abs/path.glb"},
        )
        assert res.status_code in (400, 403)
        detail = str(res.json().get("detail", ""))
        assert detail.strip() != ""
        assert str(python_root) not in detail

    @pytest.mark.asyncio
    async def test_open_valid_identity_is_deterministic_under_repeated_calls(
        self,
        client: AsyncClient,
    ) -> None:
        payload = {"kind": "enemy", "family": "alpha", "version_id": "alpha_live_00"}
        results: list[dict[str, object]] = []
        for _ in range(_DETERMINISM_REPEAT_COUNT):
            res = await client.post("/api/registry/model/load_existing/open", json=payload)
            assert res.status_code == 200
            results.append(res.json())
        assert all(result == results[0] for result in results[1:])

    @pytest.mark.asyncio
    async def test_open_missing_or_stale_registry_reference_returns_404(
        self,
        client: AsyncClient,
        python_root: pathlib.Path,
    ) -> None:
        missing_registry = await client.post(
            "/api/registry/model/load_existing/open",
            json={"kind": "enemy", "family": "alpha", "version_id": "does_not_exist"},
        )
        assert missing_registry.status_code == 404

        # Stale file reference: registry row exists but file is absent at open time.
        stale_path = python_root / "animated_exports" / "alpha_live_00.glb"
        if stale_path.exists():
            stale_path.unlink()

        stale_file = await client.post(
            "/api/registry/model/load_existing/open",
            json={"kind": "enemy", "family": "alpha", "version_id": "alpha_live_00"},
        )
        assert stale_file.status_code == 404

