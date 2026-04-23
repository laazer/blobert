### [M901-11-registry-path-policy-unification] SPECIFICATION — service module target ambiguity
**Would have asked:** Should the implementation target `blobert_asset_gen.services.registry` exclusively now, or preserve compatibility with transitional `asset_generation/python/src/model_registry/service.py` while unifying policy behavior?
**Assumption made:** Freeze behavior-level contract independent of physical module path; allow implementation to land in either location so long as one authoritative API and identical outcomes are preserved.
**Confidence:** High

### [M901-11-registry-path-policy-unification] SPECIFICATION — extension baseline ambiguity
**Would have asked:** Should extension policy be tightened beyond current endpoint behavior (for example stricter single-extension rules), or preserved unless security bypass is demonstrated?
**Assumption made:** Preserve existing valid-path behavior where safe; only tighten behavior when input is unsafe or ambiguous under traversal/encoding/extension-spoof conditions.
**Confidence:** Medium
