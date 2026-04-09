# Data Flows

High-value data flows for AI agents working in this repository.

## Asset editor request flow

```mermaid
flowchart LR
  webFrontend[WebFrontendDevServer_5173] -->|HTTP_API_calls| apiBackend[FastAPIBackend_8000]
  apiBackend -->|route_dispatch| routerModules[routers_files_run_assets_meta_registry]
  routerModules -->|registry_calls| modelRegistry[python_model_registry_service]
  modelRegistry -->|results| apiBackend
  apiBackend -->|JSON_response| webFrontend
```

## Godot and asset pipeline flow

```mermaid
flowchart LR
  generationCode[asset_generation_python] -->|generated_assets| generatedFiles[generated_glb_and_attack_json]
  generatedFiles -->|import_or_wrap| godotProject[godot_scenes_and_scripts]
  godotProject -->|headless_tests| testRunner[tests_run_tests_gd]
```

## Operational notes

- Frontend and backend are started together by `task editor` / `bash asset_generation/web/start.sh`.
- Backend router modules are part of one app process (`main:app`), not independent services.
- Generated assets should not be modified casually; regenerate intentionally when needed.
