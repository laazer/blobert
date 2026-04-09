# M9-EBPE — Enemy body-part extras

### [M9-EBPE] PLANNING — scope
**Would have asked:** Should single-ticket autopilot move the file from `backlog/` when the file was untracked?
**Assumption made:** Used `mv` to `in_progress/`; `git mv` failed for untracked file.
**Confidence:** High

### [M9-EBPE] SPEC — horns placement
**Would have asked:** Confirm horns only on `head` vs any zone.
**Assumption made:** Spec defines `horns` as head-only; non-head `horns` coerced to `none` per written spec.
**Confidence:** High

### [M9-EBPE] IMPLEMENTATION — shell geometry
**Would have asked:** Minimal shell mesh for carapace in v1?
**Assumption made:** `shell` is stub no-op geometry everywhere; options round-trip; matrix documented in spec.
**Confidence:** High
