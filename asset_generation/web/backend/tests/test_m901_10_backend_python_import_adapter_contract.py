from __future__ import annotations

import importlib
import json
import sys
import types
from pathlib import Path

import pytest


def _remove_backend_module_cache() -> None:
    for name in (
        "services.python_bridge",
        "routers.meta",
        "routers.registry",
        "routers.assets",
    ):
        sys.modules.pop(name, None)


class TestPythonBridgeContract:
    @pytest.mark.asyncio
    async def test_resolve_python_root_defaults_to_src_layout(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _remove_backend_module_cache()
        bridge = importlib.import_module("services.python_bridge")

        src_root = tmp_path / "asset_generation" / "python" / "src"
        src_root.mkdir(parents=True)
        monkeypatch.setattr(bridge, "BACKEND_DIR", tmp_path / "asset_generation" / "web" / "backend")

        resolved = bridge.resolve_python_root()
        assert resolved == src_root

    @pytest.mark.asyncio
    async def test_resolve_python_root_accepts_future_blobert_package_root(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _remove_backend_module_cache()
        bridge = importlib.import_module("services.python_bridge")

        package_root = tmp_path / "asset_generation" / "python" / "blobert_asset_gen"
        package_root.mkdir(parents=True)
        monkeypatch.setattr(bridge, "BACKEND_DIR", tmp_path / "asset_generation" / "web" / "backend")
        monkeypatch.setenv("BLOBERT_ASSET_PYTHON_ROOT", str(package_root))

        resolved = bridge.resolve_python_root()
        assert resolved == package_root

    @pytest.mark.asyncio
    async def test_bootstrap_is_idempotent_without_duplicate_sys_path_entries(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _remove_backend_module_cache()
        bridge = importlib.import_module("services.python_bridge")

        src_root = tmp_path / "asset_generation" / "python" / "src"
        src_root.mkdir(parents=True)
        monkeypatch.setenv("BLOBERT_ASSET_PYTHON_ROOT", str(src_root))

        bridge.bootstrap_python_runtime()
        bridge.bootstrap_python_runtime()

        assert sys.path.count(str(src_root)) == 1

    @pytest.mark.asyncio
    async def test_bootstrap_fails_closed_when_no_root_is_resolvable(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _remove_backend_module_cache()
        bridge = importlib.import_module("services.python_bridge")
        monkeypatch.delenv("BLOBERT_ASSET_PYTHON_ROOT", raising=False)
        monkeypatch.setattr(bridge, "BACKEND_DIR", Path("/nonexistent/backend"))

        with pytest.raises(bridge.UnresolvedPythonRootError):
            bridge.bootstrap_python_runtime()

    @pytest.mark.asyncio
    async def test_import_failure_uses_adapter_error_taxonomy(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _remove_backend_module_cache()
        bridge = importlib.import_module("services.python_bridge")
        src_root = tmp_path / "asset_generation" / "python" / "src"
        src_root.mkdir(parents=True)
        monkeypatch.setenv("BLOBERT_ASSET_PYTHON_ROOT", str(src_root))

        with pytest.raises(bridge.AssetModuleImportError):
            bridge.import_asset_module("src.definitely_missing_module")

    @pytest.mark.asyncio
    async def test_resolve_python_root_rejects_non_directory_override(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _remove_backend_module_cache()
        bridge = importlib.import_module("services.python_bridge")
        override_file = tmp_path / "not_a_directory.txt"
        override_file.write_text("x", encoding="utf-8")
        monkeypatch.setenv("BLOBERT_ASSET_PYTHON_ROOT", str(override_file))

        # CHECKPOINT: invalid override paths must fail closed with invalid-layout taxonomy,
        # not silently downgrade to an implicit fallback root.
        with pytest.raises(bridge.InvalidPythonRootLayoutError):
            bridge.resolve_python_root()

    @pytest.mark.asyncio
    async def test_import_asset_module_rejects_relative_module_traversal(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _remove_backend_module_cache()
        bridge = importlib.import_module("services.python_bridge")
        src_root = tmp_path / "asset_generation" / "python" / "src"
        src_root.mkdir(parents=True)
        monkeypatch.setenv("BLOBERT_ASSET_PYTHON_ROOT", str(src_root))

        # CHECKPOINT: adapter import boundary must reject traversal-style module requests.
        with pytest.raises(bridge.AssetModuleImportError):
            bridge.import_asset_module("..src.model_registry.service")

    @pytest.mark.asyncio
    async def test_bootstrap_concurrent_calls_are_single_effect_and_repeatable(
        self,
        tmp_path: Path,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        from concurrent.futures import ThreadPoolExecutor

        _remove_backend_module_cache()
        bridge = importlib.import_module("services.python_bridge")
        src_root = tmp_path / "asset_generation" / "python" / "src"
        src_root.mkdir(parents=True)
        monkeypatch.setenv("BLOBERT_ASSET_PYTHON_ROOT", str(src_root))

        # CHECKPOINT: multi-router startup can trigger bootstrap concurrently; contract
        # requires deterministic idempotency and no duplicated global-path side effects.
        def _bootstrap_once() -> None:
            bridge.bootstrap_python_runtime()

        with ThreadPoolExecutor(max_workers=8) as pool:
            for future in [pool.submit(_bootstrap_once) for _ in range(40)]:
                future.result()

        assert sys.path.count(str(src_root)) == 1


class TestRouterAdapterSeams:
    @pytest.mark.asyncio
    async def test_meta_router_uses_adapter_import_bridge(self, monkeypatch: pytest.MonkeyPatch) -> None:
        _remove_backend_module_cache()

        build_options_module = types.SimpleNamespace(
            animated_build_controls_for_api=lambda: {"spider": [{"key": "eye_count"}]},
        )
        config_module = types.SimpleNamespace(
            animated_enemies_for_api=lambda: [{"slug": "spider", "label": "Spider"}],
        )

        imported: list[str] = []

        def _import_asset_module(module_name: str):
            imported.append(module_name)
            if module_name == "src.utils.build_options":
                return build_options_module
            if module_name == "src.utils.config":
                return config_module
            raise RuntimeError(f"unexpected module {module_name}")

        bridge_module = types.SimpleNamespace(
            bootstrap_python_runtime=lambda: None,
            import_asset_module=_import_asset_module,
        )
        monkeypatch.setitem(sys.modules, "services.python_bridge", bridge_module)

        meta_router = importlib.import_module("routers.meta")
        response = await meta_router.get_enemies()
        body = json.loads(response.body)

        assert response.status_code == 200
        assert body["meta_backend"] == "ok"
        assert body["enemies"] == [{"slug": "spider", "label": "Spider"}]
        assert "src.utils.build_options" in imported
        assert "src.utils.config" in imported

    @pytest.mark.asyncio
    async def test_registry_router_load_service_uses_adapter(self, monkeypatch: pytest.MonkeyPatch) -> None:
        _remove_backend_module_cache()

        service_module = types.SimpleNamespace(load_effective_manifest=lambda _root: {"schema_version": 1})
        imported: list[str] = []

        def _import_asset_module(module_name: str):
            imported.append(module_name)
            if module_name == "src.model_registry.service":
                return service_module
            raise RuntimeError(f"unexpected module {module_name}")

        bridge_module = types.SimpleNamespace(
            bootstrap_python_runtime=lambda: None,
            import_asset_module=_import_asset_module,
        )
        monkeypatch.setitem(sys.modules, "services.python_bridge", bridge_module)

        registry_router = importlib.import_module("routers.registry")
        loaded = registry_router._load_service()

        assert loaded is service_module
        assert imported == ["src.model_registry.service"]

    @pytest.mark.asyncio
    async def test_assets_router_texture_endpoint_uses_adapter_loader(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _remove_backend_module_cache()

        texture_loader_module = types.SimpleNamespace(
            get_available_assets=lambda: [
                {
                    "id": "stripe_a",
                    "filename": "stripe_a.png",
                    "display_name": "Stripe A",
                    "description": "adapter-seam",
                    "layout": "uv",
                    "width": 64,
                    "height": 64,
                    "tiling_supported": True,
                },
            ],
        )
        imported: list[str] = []

        def _import_asset_module(module_name: str):
            imported.append(module_name)
            if module_name == "src.utils.texture_asset_loader":
                return texture_loader_module
            raise RuntimeError(f"unexpected module {module_name}")

        bridge_module = types.SimpleNamespace(
            bootstrap_python_runtime=lambda: None,
            import_asset_module=_import_asset_module,
        )
        monkeypatch.setitem(sys.modules, "services.python_bridge", bridge_module)

        assets_router = importlib.import_module("routers.assets")
        response = await assets_router.get_texture_assets()
        body = json.loads(response.body)

        assert response.status_code == 200
        assert body == {
            "textures": [
                {
                    "id": "stripe_a",
                    "filename": "stripe_a.png",
                    "display_name": "Stripe A",
                    "description": "adapter-seam",
                    "layout": "uv",
                    "width": 64,
                    "height": 64,
                    "tiling_supported": True,
                },
            ],
        }
        assert imported == ["src.utils.texture_asset_loader"]

    @pytest.mark.asyncio
    async def test_registry_router_load_service_does_not_cache_failed_imports(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        _remove_backend_module_cache()

        attempts = {"count": 0}

        def _import_asset_module(module_name: str):
            if module_name != "src.model_registry.service":
                raise RuntimeError(f"unexpected module {module_name}")
            attempts["count"] += 1
            if attempts["count"] == 1:
                raise RuntimeError("transient import failure")
            return types.SimpleNamespace(load_effective_manifest=lambda _root: {"schema_version": 1})

        bridge_module = types.SimpleNamespace(
            bootstrap_python_runtime=lambda: None,
            import_asset_module=_import_asset_module,
        )
        monkeypatch.setitem(sys.modules, "services.python_bridge", bridge_module)

        registry_router = importlib.import_module("routers.registry")
        with pytest.raises(RuntimeError):
            registry_router._load_service()
        loaded = registry_router._load_service()

        # CHECKPOINT: a failed adapter import must not poison router-level service loading.
        assert loaded.load_effective_manifest(None) == {"schema_version": 1}
        assert attempts["count"] == 2
