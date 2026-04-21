### [M901-02] SPECIFICATION — dependency direction for SCHEMA_VERSION
**Would have asked:** Should `SCHEMA_VERSION` live in `schema.py` or `migrations.py` when `validate_manifest` must call legacy normalizers in `migrations` without creating an import cycle?
**Assumption made:** Own `SCHEMA_VERSION` in `migrations.py`; `schema.py` imports it from `migrations`; `migrations` must not import `schema`. Documented in `project_board/specs/m901_02_model_registry_layering_spec.md` Requirement R1/R2/R4.
**Confidence:** High
