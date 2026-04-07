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

import core.config as config_module
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
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


# ---------------------------------------------------------------------------
# Adversarial / Test-Breaker extensions
# (Added by Test Breaker Agent — run-2026-04-07T03-00-00Z-test-break)
# ---------------------------------------------------------------------------


class TestAdversarialPathJail:
    """
    Adversarial path-jail tests targeting mutation scenarios, double-encoding,
    null bytes, and coverage gaps identified by the Test Breaker agent.
    """

    @pytest.fixture(autouse=True)
    def _setup_python_root(self, python_root: pathlib.Path):
        """Sentinel file at root level and a real GLB inside animated_exports."""
        (python_root / "main.py").write_text("# sentinel")
        animated = python_root / "animated_exports"
        animated.mkdir(parents=True, exist_ok=True)
        (animated / "real_file.glb").write_bytes(b"\x00" * 8)

    @pytest.mark.asyncio
    async def test_null_byte_in_path_does_not_serve_file(self, client: AsyncClient):
        """
        ARGLB-3 risk — null byte injection: animated_exports/file.glb%00.txt must not serve the file.

        # CHECKPOINT (run-2026-04-07T03-00-00Z-test-break)
        Implementation gap confirmed: `pathlib.Path.resolve()` raises ValueError for
        embedded null bytes, but this ValueError is NOT inside the try/except block in
        assets.py (which only wraps `relative_to()`, not `resolve()`). The unhandled
        ValueError propagates through all ASGI middleware and raises out of httpx's
        ASGI transport — the test never receives an HTTP response at all.

        Security impact: the server crashes (unhandled exception) rather than returning
        a clean 400. This is NOT a silent bypass — no file is served — but it exposes
        the server to a DoS vector via crafted null-byte URLs.

        Required fix in assets.py:
            try:
                resolved = (python_root / asset_path).resolve()
                resolved.relative_to(python_root)
            except (ValueError, OSError):
                raise HTTPException(400, "Path outside allowed directories")

        This test verifies the security property (file not served) by asserting that
        either a 4xx/5xx HTTP response is returned OR a ValueError/RuntimeError is
        raised (confirming the server rejected the request rather than serving the file).

        Vulnerability exposed: if the null byte were silently stripped, `real_file.glb`
        would be served under a path the guard validated as `real_file.glb%00.txt`
        (extension `.txt` not `.glb`) — bypassing MIME extension checks.
        """
        try:
            response = await client.get("/api/assets/animated_exports/real_file.glb%00.txt")
            # If we get here, must not be 200 (no file must be served)
            assert response.status_code != 200, (
                "Null byte injection was silently handled and returned 200 — "
                "file was served despite null byte in path"
            )
        except (ValueError, RuntimeError):
            # Unhandled exception from pathlib propagated through ASGI — confirms
            # the file was NOT served; documents implementation gap (should be 400)
            pass

    @pytest.mark.asyncio
    async def test_null_byte_in_path_should_return_400_not_raise(self, client: AsyncClient):
        """
        ARGLB-3 risk — null byte injection: must return HTTP 400, not raise unhandled exception.

        This test is EXPECTED TO FAIL until the implementation wraps resolve() in the
        try/except block. The current implementation allows the ValueError from
        pathlib.Path.resolve() to propagate out of the route handler, crashing the
        server process (unhandled 500 in production, exception in test).

        The correct fix extends the try/except to cover resolve():
            try:
                resolved = (python_root / asset_path).resolve()
                resolved.relative_to(python_root)
            except (ValueError, OSError):
                raise HTTPException(status_code=400, detail="Path outside allowed directories")
        """
        response = await client.get("/api/assets/animated_exports/real_file.glb%00.txt")
        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_double_encoded_traversal_returns_403(self, client: AsyncClient):
        """
        ARGLB-3 risk — double-encoded traversal: %252e%252e decodes to literal %2e%2e.

        # CHECKPOINT (run-2026-04-07T03-00-00Z-test-break)
        FastAPI decodes percent-encoding once: %252e → %2e (literal text, NOT a dot).
        Path guard receives "%2e%2e/main.py"; Path("%2e%2e") resolves within python_root
        (layer 1 passes), but "%2e%2e" is not in _EXPORT_DIRS (layer 2 → 403).
        This verifies double-encoding does NOT bypass the path jail to serve a file.
        """
        response = await client.get("/api/assets/%252e%252e/main.py")
        assert response.status_code == 403

    @pytest.mark.asyncio
    async def test_directory_as_path_returns_404_strict(
        self, client: AsyncClient, python_root: pathlib.Path  # noqa: ARG002
    ):
        """
        ARGLB-3.5 — Strict assertion: directory path returns 404, not 500.

        # CHECKPOINT (run-2026-04-07T03-00-00Z-test-break)
        The existing test_directory_path_returns_non_200 only asserts != 200 to
        accommodate the current 500 behavior. This adversarial test exposes the
        implementation gap precisely: without an explicit `resolved.is_file()` check,
        FileResponse raises RuntimeError on directories (500). This test is expected
        to fail until the implementation agent adds `if not resolved.is_file(): raise
        HTTPException(404)` before constructing FileResponse.
        """
        response = await client.get("/api/assets/animated_exports/")
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_within_jail_traversal_via_encoded_dots_returns_400(
        self, client: AsyncClient
    ):
        """
        ARGLB-3.7 — Traversal via animated_exports/%2e%2e/animated_exports/real_file.glb.

        A path that exits the export dir and re-enters it via traversal. Because the
        resolved path ends up back within python_root and under animated_exports, layers
        1 and 2 pass — but the traversal segment `..` must still be blocked at layer 1
        since the intermediate resolved path escapes animated_exports.

        Mutation risk: a naive jail that only checks the final resolved path (not the
        intermediate) would serve this file. The correct implementation resolves
        `python_root / asset_path` and checks `relative_to(python_root)` — which passes
        here because the final path IS within python_root. This test documents that the
        implementation allows semantically-equivalent paths that traverse through `..`
        as long as they resolve correctly, rather than rejecting all paths with `..`
        segments. If the guard detects `..` syntactically, this returns 400; if it only
        resolves, this returns 200 (the file is served). Both are acceptable per spec
        (spec only mandates traversal that ESCAPES python_root → 400). Documents behavior.
        """
        # %2e%2e is decoded to ".." by FastAPI; the resolved path goes out of
        # animated_exports but stays in python_root, then re-enters animated_exports.
        response = await client.get(
            "/api/assets/animated_exports/%2e%2e/animated_exports/real_file.glb"
        )
        # Must not be a server error (500). Either 400 (guard rejects ..) or 200 (file served).
        assert response.status_code in (200, 400)
        assert response.status_code != 500

    @pytest.mark.asyncio
    async def test_path_component_that_is_only_dots_not_traversal(
        self, client: AsyncClient, python_root: pathlib.Path
    ):
        """
        Mutation test — a directory literally named ".." inside an export dir.

        If animated_exports contains a directory named "..", Path.resolve() would
        canonicalize it and the resolve-based guard would catch the traversal.
        This confirms the guard uses resolve() semantics, not string matching.
        """
        animated = python_root / "animated_exports"
        # Create a directory named ".." is not possible on most filesystems;
        # instead test a directory named "..." (three dots) which IS valid.
        dotdir = animated / "..."
        dotdir.mkdir(parents=True, exist_ok=True)
        (dotdir / "file.glb").write_bytes(b"\x00" * 4)

        # "..." is a valid directory name; this path should be 200 or 404 (not 400 or 403)
        # because "..." does not escape the jail — it is a literal directory name.
        response = await client.get("/api/assets/animated_exports/.../file.glb")
        assert response.status_code in (200, 404)
        assert response.status_code != 400
        assert response.status_code != 403


class TestAdversarialListEndpoint:
    """
    Adversarial list endpoint tests: empty dirs, non-.glb/.json content,
    stress volume, and edge-case filenames.
    """

    @pytest.mark.asyncio
    async def test_list_empty_when_export_dirs_exist_but_have_no_glb_or_json(
        self, python_root: pathlib.Path, client: AsyncClient
    ):
        """
        ARGLB-1.5 mutation — export dirs exist but contain only non-.glb/.json files.

        # CHECKPOINT (run-2026-04-07T03-00-00Z-test-break)
        Verifies the MIME filter `f.suffix in _MIME` is not accidentally bypassed.
        If an implementation mutation changed `in _MIME` to `not in _MIME` or removed
        the filter entirely, this test would catch it: exports/ has only .txt and .bin
        files, so the list must be empty.
        """
        exports = python_root / "exports"
        exports.mkdir(parents=True, exist_ok=True)
        (exports / "notes.txt").write_text("ignored")
        (exports / "data.bin").write_bytes(b"\xde\xad\xbe\xef")
        (exports / "config.yaml").write_text("ignored: true")

        response = await client.get("/api/assets")
        assert response.status_code == 200
        assert response.json() == {"assets": []}

    @pytest.mark.asyncio
    async def test_list_dotfile_glb_excluded_by_python39_suffix_behavior(
        self, python_root: pathlib.Path, client: AsyncClient
    ):
        """
        ARGLB-1 edge case — file named '.glb' (dotfile): spec-vs-implementation gap.

        The spec notes this file "will appear in the list" because "Path.suffix returns
        '.glb'". This is INCORRECT for Python 3.9: `Path(".glb").suffix` returns `""`
        (empty string), not `".glb"`. Python 3.9 treats `.glb` as a dotfile with stem
        `.glb` and no extension. The `f.suffix in _MIME` filter therefore EXCLUDES this
        file because `"" not in _MIME`.

        This test documents the spec inaccuracy and asserts the actual Python 3.9
        behavior: the dotfile `.glb` is NOT included in the list. The spec must be
        corrected to note that dotfile behavior is Python-version-dependent.

        Python 3.12+ behavior: `Path(".glb").suffix` → `""` (same — no change).
        This is consistent across all current Python versions for dotfiles.
        """
        animated = python_root / "animated_exports"
        animated.mkdir(parents=True, exist_ok=True)
        (animated / ".glb").write_bytes(b"\x00" * 4)

        response = await client.get("/api/assets")
        assets = response.json()["assets"]
        names = [a["name"] for a in assets]
        # Dotfile .glb has empty suffix in Python — excluded by MIME filter
        assert ".glb" not in names

    @pytest.mark.asyncio
    async def test_list_stress_50_files_all_returned(
        self, python_root: pathlib.Path, client: AsyncClient
    ):
        """
        Stress test — 50 .glb files in animated_exports are all returned.

        Exposes any implicit pagination, truncation, or count limit in the list endpoint.
        If the implementation iterates with a hidden limit (e.g., islice), this test
        will catch it.
        """
        animated = python_root / "animated_exports"
        animated.mkdir(parents=True, exist_ok=True)
        for i in range(50):
            (animated / f"model_{i:03d}.glb").write_bytes(b"\x00" * 8)

        response = await client.get("/api/assets")
        assert response.status_code == 200
        assets = response.json()["assets"]
        assert len(assets) == 50

    @pytest.mark.asyncio
    async def test_list_files_sorted_within_dir(
        self, python_root: pathlib.Path, client: AsyncClient
    ):
        """
        ARGLB-1 constraint — files within a single export dir are name-sorted (ascending).

        Mutation risk: if `sorted()` is removed from the implementation, files appear
        in filesystem iteration order (non-deterministic). This test writes files in
        reverse alphabetical order and confirms sorted output.
        """
        animated = python_root / "animated_exports"
        animated.mkdir(parents=True, exist_ok=True)
        # Write in reverse alpha order
        for name in ["z_model.glb", "m_model.glb", "a_model.glb"]:
            (animated / name).write_bytes(b"\x00" * 4)

        response = await client.get("/api/assets")
        assets = response.json()["assets"]
        names = [a["name"] for a in assets]
        assert names == sorted(names)

    @pytest.mark.asyncio
    async def test_list_multiple_dirs_each_internally_sorted(
        self, python_root: pathlib.Path, client: AsyncClient
    ):
        """
        ARGLB-1.8 constraint — inter-dir ordering preserved; intra-dir sorted.

        Mutation test: verifies both the canonical dir order AND per-dir sort are
        maintained simultaneously. If implementation sorts globally across dirs,
        the canonical dir order (animated_exports before exports) could break.
        """
        for d_name in ["animated_exports", "exports"]:
            d = python_root / d_name
            d.mkdir(parents=True, exist_ok=True)
            # z_ prefix in animated_exports and a_ prefix in exports: global sort
            # would put exports files first, violating canonical order.
            prefix = "z" if d_name == "animated_exports" else "a"
            for i in range(3):
                (d / f"{prefix}_file_{i}.glb").write_bytes(b"\x00" * 4)

        response = await client.get("/api/assets")
        assets = response.json()["assets"]
        dirs_seen = [a["dir"] for a in assets]
        # All animated_exports entries must precede all exports entries
        animated_indices = [i for i, d in enumerate(dirs_seen) if d == "animated_exports"]
        exports_indices = [i for i, d in enumerate(dirs_seen) if d == "exports"]
        assert max(animated_indices) < min(exports_indices)


class TestAdversarialMimeTypes:
    """
    Adversarial MIME type tests: uppercase extensions, extension mutations,
    and octet-stream fallback verification.
    """

    @pytest.fixture(autouse=True)
    def _setup_export_dir(self, python_root: pathlib.Path):
        animated = python_root / "animated_exports"
        animated.mkdir(parents=True, exist_ok=True)
        (animated / "model.GLB").write_bytes(b"\x00" * 8)
        (animated / "config.JSON").write_text('{"x": 1}')
        (animated / "archive.tar.gz").write_bytes(b"\x1f\x8b" + b"\x00" * 6)

    @pytest.mark.asyncio
    async def test_uppercase_glb_extension_returns_octet_stream(self, client: AsyncClient):
        """
        ARGLB-2 edge case — .GLB (uppercase) returns application/octet-stream, not gltf-binary.

        # CHECKPOINT (run-2026-04-07T03-00-00Z-test-break)
        Path.suffix is case-sensitive; '.GLB' is not in _MIME dict. This test prevents
        a mutation that adds case-insensitive MIME lookup (which would incorrectly serve
        .GLB files with model/gltf-binary — violating the spec's explicit note that
        MIME type is determined solely by Path.suffix, case-sensitive).
        """
        response = await client.get("/api/assets/animated_exports/model.GLB")
        assert response.status_code == 200
        content_type = response.headers["content-type"].split(";")[0].strip()
        assert content_type == "application/octet-stream"

    @pytest.mark.asyncio
    async def test_uppercase_json_extension_returns_octet_stream(self, client: AsyncClient):
        """
        ARGLB-2 edge case — .JSON (uppercase) returns application/octet-stream, not application/json.

        Same case-sensitivity mutation guard as uppercase GLB test.
        """
        response = await client.get("/api/assets/animated_exports/config.JSON")
        assert response.status_code == 200
        content_type = response.headers["content-type"].split(";")[0].strip()
        assert content_type == "application/octet-stream"

    @pytest.mark.asyncio
    async def test_double_extension_uses_last_suffix(self, client: AsyncClient):
        """
        Mutation test — file.tar.gz: Path.suffix returns '.gz', not '.tar'.

        Exposes any mutation that uses Path.suffixes[-1] vs Path.suffix or uses
        the full filename for MIME detection. Neither '.gz' nor '.tar' is in _MIME,
        so octet-stream must be returned. This also verifies no double-extension
        confusion can bypass the jail.
        """
        response = await client.get("/api/assets/animated_exports/archive.tar.gz")
        assert response.status_code == 200
        content_type = response.headers["content-type"].split(";")[0].strip()
        assert content_type == "application/octet-stream"


class TestAdversarialMimeTypesWithGlb:
    """Adversarial MIME tests that need a real .glb file (not .GLB)."""

    @pytest.fixture(autouse=True)
    def _setup(self, python_root: pathlib.Path):
        animated = python_root / "animated_exports"
        animated.mkdir(parents=True, exist_ok=True)
        self._glb_path = animated / "model.glb"
        self._glb_path.write_bytes(b"\x00" * 16)

    @pytest.mark.asyncio
    async def test_glb_content_type_has_no_charset_parameter(self, client: AsyncClient):
        """
        ARGLB-2.4 mutation — model/gltf-binary must not have charset= parameter appended.

        A mutation introducing a text-type wrapper or incorrect media_type string would
        cause FastAPI to append '; charset=utf-8'. GLB consumers (three.js useGLTF) do
        not tolerate charset in the content-type for binary formats.
        """
        response = await client.get("/api/assets/animated_exports/model.glb")
        assert response.status_code == 200
        content_type = response.headers["content-type"]
        assert "charset" not in content_type.lower()
        assert content_type.strip() == "model/gltf-binary"
