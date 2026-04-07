"""
Behavioral tests for routers/assets.py.

Spec traceability:
  ARGLB-1 — Assets List Endpoint Response Schema
  ARGLB-2 — MIME Type Contract
  ARGLB-3 — Path-Jail Rejection Rules

All tests use httpx.AsyncClient with ASGITransport(app=app).
settings.python_root is patched per-test via monkeypatch to point at a
controlled tmp directory so tests are fully deterministic and isolated.

Run from asset_generation/web/backend/:
    python -m pytest tests/test_assets_router.py -v
"""

import pathlib

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

import core.config as config_module
from main import app

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_export_tree(tmp_path: pathlib.Path) -> pathlib.Path:
    """Create a minimal export directory tree under tmp_path/python/."""
    python_root = tmp_path / "python"
    animated = python_root / "animated_exports"
    animated.mkdir(parents=True)
    return python_root


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def python_root(tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch) -> pathlib.Path:
    """
    Patch settings.python_root to a fresh tmp directory and return it.

    Each test that needs files on disk creates them under the returned path.
    """
    root = tmp_path / "python"
    root.mkdir(parents=True)
    monkeypatch.setattr(config_module.settings, "python_root", root)
    return root


@pytest_asyncio.fixture()
async def client(python_root: pathlib.Path):  # noqa: ARG001  — ensures patch applied first
    """Async HTTP client backed by the FastAPI app under test."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


# ---------------------------------------------------------------------------
# ARGLB-1 — Assets List Endpoint Response Schema
# ---------------------------------------------------------------------------


class TestListEndpointSchema:
    """ARGLB-1.1 / ARGLB-1.2 / ARGLB-1.3: basic response shape."""

    @pytest.mark.asyncio
    async def test_list_returns_200_and_json_content_type(self, client: AsyncClient):
        """ARGLB-1.1 — GET /api/assets returns HTTP 200 with application/json."""
        response = await client.get("/api/assets")
        assert response.status_code == 200
        assert "application/json" in response.headers["content-type"]

    @pytest.mark.asyncio
    async def test_list_response_has_assets_key(self, client: AsyncClient):
        """ARGLB-1.2 — Response body is {"assets": [...]}."""
        response = await client.get("/api/assets")
        body = response.json()
        assert "assets" in body
        assert isinstance(body["assets"], list)

    @pytest.mark.asyncio
    async def test_list_entry_has_exact_keys(
        self, python_root: pathlib.Path, client: AsyncClient
    ):
        """ARGLB-1.3 — Each asset entry has exactly path, name, dir, size."""
        animated = python_root / "animated_exports"
        animated.mkdir(parents=True, exist_ok=True)
        (animated / "test.glb").write_bytes(b"\x00" * 16)

        response = await client.get("/api/assets")
        assets = response.json()["assets"]
        assert len(assets) == 1
        assert set(assets[0].keys()) == {"path", "name", "dir", "size"}

    @pytest.mark.asyncio
    async def test_list_entry_values_for_glb_file(
        self, python_root: pathlib.Path, client: AsyncClient
    ):
        """ARGLB-1.4 — Correct field values for a known .glb file."""
        animated = python_root / "animated_exports"
        animated.mkdir(parents=True, exist_ok=True)
        glb_content = b"\x00" * 24
        (animated / "adhesion_bug_animated_00.glb").write_bytes(glb_content)

        response = await client.get("/api/assets")
        assets = response.json()["assets"]
        assert len(assets) == 1
        entry = assets[0]
        assert entry["path"] == "animated_exports/adhesion_bug_animated_00.glb"
        assert entry["name"] == "adhesion_bug_animated_00.glb"
        assert entry["dir"] == "animated_exports"
        assert entry["size"] == len(glb_content)

    @pytest.mark.asyncio
    async def test_list_includes_json_excludes_txt(
        self, python_root: pathlib.Path, client: AsyncClient
    ):
        """ARGLB-1.5 — .json files are included; .txt files are not."""
        animated = python_root / "animated_exports"
        animated.mkdir(parents=True, exist_ok=True)
        (animated / "meta.json").write_text('{"x": 1}')
        (animated / "notes.txt").write_text("ignored")

        response = await client.get("/api/assets")
        assets = response.json()["assets"]
        names = [a["name"] for a in assets]
        assert "meta.json" in names
        assert "notes.txt" not in names

    @pytest.mark.asyncio
    async def test_list_empty_when_all_export_dirs_absent(
        self, python_root: pathlib.Path, client: AsyncClient  # noqa: ARG002
    ):
        """ARGLB-1.6 — No export dirs on disk → {"assets": []}."""
        # python_root exists but contains no export subdirectories
        response = await client.get("/api/assets")
        assert response.status_code == 200
        assert response.json() == {"assets": []}

    @pytest.mark.asyncio
    async def test_list_partial_dirs_only_returns_existing(
        self, python_root: pathlib.Path, client: AsyncClient
    ):
        """ARGLB-1.7 — Only existing export dirs contribute to the list."""
        # Only animated_exports exists; exports/, player_exports/, level_exports/ do not
        animated = python_root / "animated_exports"
        animated.mkdir(parents=True, exist_ok=True)
        (animated / "a.glb").write_bytes(b"\x00" * 8)

        response = await client.get("/api/assets")
        assets = response.json()["assets"]
        assert all(a["dir"] == "animated_exports" for a in assets)
        assert len(assets) == 1

    @pytest.mark.asyncio
    async def test_list_canonical_dir_order(
        self, python_root: pathlib.Path, client: AsyncClient
    ):
        """ARGLB-1.8 — animated_exports before exports before player_exports before level_exports."""
        for d in ["animated_exports", "exports", "player_exports", "level_exports"]:
            subdir = python_root / d
            subdir.mkdir(parents=True, exist_ok=True)
            (subdir / f"{d}_file.glb").write_bytes(b"\x00" * 4)

        response = await client.get("/api/assets")
        assets = response.json()["assets"]
        dirs_in_order = [a["dir"] for a in assets]
        expected_order = [
            "animated_exports",
            "exports",
            "player_exports",
            "level_exports",
        ]
        assert dirs_in_order == expected_order

    @pytest.mark.asyncio
    async def test_list_excludes_subdirectories_inside_export_dir(
        self, python_root: pathlib.Path, client: AsyncClient
    ):
        """ARGLB-1 constraint — subdirectories inside export dirs are not listed."""
        animated = python_root / "animated_exports"
        animated.mkdir(parents=True, exist_ok=True)
        (animated / "file.glb").write_bytes(b"\x00" * 4)
        subdir = animated / "subdir"
        subdir.mkdir()
        (subdir / "nested.glb").write_bytes(b"\x00" * 4)

        response = await client.get("/api/assets")
        assets = response.json()["assets"]
        # The subdirectory entry "subdir" must not appear; nested.glb must not appear
        names = [a["name"] for a in assets]
        assert "subdir" not in names
        assert "nested.glb" not in names
        assert "file.glb" in names

    @pytest.mark.asyncio
    async def test_list_size_field_is_integer(
        self, python_root: pathlib.Path, client: AsyncClient
    ):
        """ARGLB-1.3 — size field must be an integer (not string or float)."""
        animated = python_root / "animated_exports"
        animated.mkdir(parents=True, exist_ok=True)
        (animated / "a.glb").write_bytes(b"\xff" * 100)

        response = await client.get("/api/assets")
        assets = response.json()["assets"]
        assert isinstance(assets[0]["size"], int)
        assert assets[0]["size"] == 100


# ---------------------------------------------------------------------------
# ARGLB-2 — MIME Type Contract
# ---------------------------------------------------------------------------


class TestMimeTypes:
    """ARGLB-2: correct Content-Type per file extension."""

    @pytest.fixture(autouse=True)
    def _setup_export_dir(self, python_root: pathlib.Path):
        """Create animated_exports with fixture files for every MIME test."""
        animated = python_root / "animated_exports"
        animated.mkdir(parents=True, exist_ok=True)
        (animated / "adhesion_bug_animated_00.glb").write_bytes(b"\x00" * 16)
        (animated / "some_config.json").write_text('{"a": 1}')
        (animated / "data.bin").write_bytes(b"\xde\xad\xbe\xef")

    @pytest.mark.asyncio
    async def test_glb_served_with_gltf_binary_mime(self, client: AsyncClient):
        """ARGLB-2.1 / ARGLB-2.4 — .glb → Content-Type: model/gltf-binary (exact)."""
        response = await client.get(
            "/api/assets/animated_exports/adhesion_bug_animated_00.glb"
        )
        assert response.status_code == 200
        assert response.headers["content-type"].startswith("model/gltf-binary")

    @pytest.mark.asyncio
    async def test_glb_mime_is_exactly_gltf_binary_not_variant(self, client: AsyncClient):
        """ARGLB-2.4 — Must be model/gltf-binary, not model/gltf+binary or application/gltf-binary."""
        response = await client.get(
            "/api/assets/animated_exports/adhesion_bug_animated_00.glb"
        )
        content_type = response.headers["content-type"]
        # Strip charset/parameters and compare base type
        base_type = content_type.split(";")[0].strip()
        assert base_type == "model/gltf-binary"

    @pytest.mark.asyncio
    async def test_json_served_with_application_json_mime(self, client: AsyncClient):
        """ARGLB-2.2 — .json → Content-Type: application/json."""
        response = await client.get("/api/assets/animated_exports/some_config.json")
        assert response.status_code == 200
        assert "application/json" in response.headers["content-type"]

    @pytest.mark.asyncio
    async def test_unknown_extension_served_with_octet_stream(self, client: AsyncClient):
        """ARGLB-2.3 — unknown extension → Content-Type: application/octet-stream."""
        response = await client.get("/api/assets/animated_exports/data.bin")
        assert response.status_code == 200
        assert "application/octet-stream" in response.headers["content-type"]


# ---------------------------------------------------------------------------
# ARGLB-3 — Path-Jail Rejection Rules
# ---------------------------------------------------------------------------


class TestPathJail:
    """ARGLB-3: traversal → 400, non-export-dir → 403, missing → 404."""

    @pytest.fixture(autouse=True)
    def _setup_python_root(self, python_root: pathlib.Path):
        """
        Place a sentinel file at the python_root level (simulating main.py)
        and create an animated_exports dir for 403/404 tests.
        """
        (python_root / "main.py").write_text("# sentinel")
        animated = python_root / "animated_exports"
        animated.mkdir(parents=True, exist_ok=True)
        (animated / "real_file.glb").write_bytes(b"\x00" * 8)

    @pytest.mark.asyncio
    async def test_double_dot_traversal_literal_returns_non_200(self, client: AsyncClient):
        """
        ARGLB-3.1 — GET /api/assets/../../main.py → must not return 200.

        Implementation gap note: httpx normalizes `..` segments in URLs before
        sending (e.g., /api/assets/../../main.py becomes /main.py), so the request
        misses the /api/assets/{path} route entirely and returns 404 via route-miss.
        The spec requires 400 from the path guard; this test will only pass once the
        implementation handles this normalization (e.g., by validating the raw URL
        path or by catching route-misses that originated from traversal attempts).
        Currently this serves as a red test documenting the implementation gap.

        The canonical traversal security test is test_url_encoded_traversal_returns_400
        (ARGLB-3.6) which is NOT normalized by httpx.
        """
        response = await client.get("/api/assets/../../main.py")
        # Spec requires 400; current behavior is 404 (route-miss after normalization)
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_single_dot_dot_traversal_literal_returns_non_200(self, client: AsyncClient):
        """
        ARGLB-3.2 — GET /api/assets/../main.py → must not return 200.

        Same normalization caveat as test_double_dot_traversal_literal_returns_non_200.
        httpx normalizes this to /api/main.py. Spec requires 400.
        """
        response = await client.get("/api/assets/../main.py")
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_url_encoded_traversal_returns_400(self, client: AsyncClient):
        """
        ARGLB-3.6 — %2e%2e%2f%2e%2e%2fmain.py URL-encoded traversal → 400.

        This is the primary path-traversal security test. httpx does NOT normalize
        percent-encoded dots, so %2e%2e reaches FastAPI, which decodes it to ..
        before the route handler receives asset_path. The Python path guard then
        catches the traversal and returns 400.
        """
        response = await client.get("/api/assets/%2e%2e%2f%2e%2e%2fmain.py")
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_url_encoded_traversal_400_has_nonempty_detail(self, client: AsyncClient):
        """ARGLB-3.1 — The 400 response from URL-encoded traversal has a non-empty detail."""
        response = await client.get("/api/assets/%2e%2e%2f%2e%2e%2fmain.py")
        assert response.status_code == 400
        body = response.json()
        assert "detail" in body
        assert isinstance(body["detail"], str)
        assert len(body["detail"]) > 0

    @pytest.mark.asyncio
    async def test_non_export_dir_returns_403(self, client: AsyncClient, python_root: pathlib.Path):
        """ARGLB-3.3 — Path into a non-allowlisted dir returns 403 even if file exists."""
        other_dir = python_root / "some_other_dir"
        other_dir.mkdir()
        (other_dir / "file.glb").write_bytes(b"\x00" * 8)

        response = await client.get("/api/assets/some_other_dir/file.glb")
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_missing_file_in_export_dir_returns_404(self, client: AsyncClient):
        """ARGLB-3.4 — Nonexistent file inside an export dir returns 404."""
        response = await client.get(
            "/api/assets/animated_exports/nonexistent_file.glb"
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_missing_file_404_detail_is_asset_not_found(self, client: AsyncClient):
        """ARGLB-3.4 — The 404 detail must be 'Asset not found'."""
        response = await client.get(
            "/api/assets/animated_exports/nonexistent_file.glb"
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "Asset not found"

    @pytest.mark.asyncio
    async def test_directory_path_returns_non_200(
        self, client: AsyncClient, python_root: pathlib.Path  # noqa: ARG002
    ):
        """
        ARGLB-3.5 — Requesting a path that resolves to a directory returns non-200.

        Spec states preferred behavior is 404; the current scaffold raises a
        RuntimeError (500) from FileResponse when the resolved path is a directory
        rather than a file. The spec requires this not be 200. The Implementation
        agent must add an explicit is_file() check before constructing FileResponse
        to return 404 cleanly.
        """
        # animated_exports/ itself is a directory; trailing slash routes to serve handler
        response = await client.get("/api/assets/animated_exports/")
        # Must not be 200; 404 preferred by spec, 500 is current behavior
        assert response.status_code != 200

    @pytest.mark.asyncio
    async def test_deeply_nested_url_encoded_traversal_returns_400(self, client: AsyncClient):
        """
        ARGLB-3.7 — Deeply nested URL-encoded traversal → 400.

        Using percent-encoded dots to ensure the traversal reaches the server-side
        path guard without httpx URL normalization stripping the .. segments.
        """
        response = await client.get(
            "/api/assets/animated_exports%2f..%2f..%2f..%2fmain.py"
        )
        assert response.status_code == 400
