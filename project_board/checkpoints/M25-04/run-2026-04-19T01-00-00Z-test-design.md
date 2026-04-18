# Checkpoint Log — M25-04 TEST_DESIGN run-2026-04-19T01-00-00Z

## [M25-04] TEST_DESIGN — ensure_blender_stubs call pattern

**Would have asked:** The task instruction says "Use `blender_stubs.ensure_blender_stubs()` at top of file (following the offset_xyz test pattern)", but the actual reference test file (`test_animated_build_options_offset_xyz.py`) does NOT call `ensure_blender_stubs()` at module level — it relies on the root `conftest.py` which already calls it. Should the new test file call it explicitly or follow the actual code pattern?

**Assumption made:** Follow the actual code pattern of the reference test file. The root `conftest.py` already calls `ensure_blender_stubs()` for all tests under `asset_generation/python/tests/`. Adding a redundant call at the test file level is harmless but not the established pattern. The test file imports match those of the reference test exactly. No explicit `ensure_blender_stubs()` call at test-file level.

**Confidence:** High

---

## [M25-04] TEST_DESIGN — PRC-3 unconditional vs conditional defaults

**Would have asked:** The spec (PRC-3, Risk section) notes that `_defaults_for_slug()` may be unconditional — meaning `player_slime` could also receive the 6 rotation keys in its defaults dict. Should the test for `_defaults_for_slug` only cover the 6 animated slugs, or also assert player_slime behavior?

**Assumption made:** Test only the 6 animated enemy slugs for `_defaults_for_slug()` rotation keys. The spec is explicit that `player_slime` exclusion is a concern of `animated_build_controls_for_api()`, not `_defaults_for_slug()`. Asserting player_slime defaults would over-specify implementation details not required by the AC.

**Confidence:** High

---

## [M25-04] TEST_DESIGN — AC-8.7 cross-slug clamp coverage

**Would have asked:** AC-8.7 says "at least 3 distinct slugs". Should all 6 be covered via parametrize?

**Assumption made:** Use pytest.mark.parametrize covering all 6 animated slugs for clamp tests (both upper and lower), satisfying AC-8.7 and PRC-5 AC-5.10 simultaneously. This is stricter than the minimum and better documents the contract.

**Confidence:** High
