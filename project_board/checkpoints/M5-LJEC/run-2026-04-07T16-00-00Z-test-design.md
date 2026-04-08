### [M5-LJEC] TEST_DESIGN — Vector stub arithmetic operators required by limb_chain

**Would have asked:** The `_Vector` stub in `blender_stubs.py` has no `__add__`, `__sub__`, `__mul__`, `__rmul__`, or `__truediv__`. `limb_chain` must perform linear interpolation: `head + (tail - head) * (i / n)`. Tests cannot construct expected `Vector` values via arithmetic either. Should tests extend the stub, or work around it?
**Assumption made:** Tests extend the `_Vector` stub locally in `conftest.py` fixtures (or in test setup) to add arithmetic operators. This is the least invasive approach: the test file patches `mathutils.Vector._t`-based arithmetic in a `conftest.py`-local fixture. Alternatively the test uses plain numeric construction `Vector((x, y, z))` for expected values since the interpolation formula is known. The strictest defensible approach: extend the stub in `blender_stubs.py` itself (since LJEC-1 spec explicitly flags this as a dependency), and assert equality using the `_t` tuple directly to avoid any stub inequality edge cases.
**Confidence:** Medium

---

### [M5-LJEC] TEST_DESIGN — test_humanoid_rig_segments.py target location

**Would have asked:** The task says write LJEC-4/5/9 tests to `test_humanoid_rig_segments.py`. The ticket's NEXT ACTION says "additions to `test_rig_ratios.py` (LJEC-4, LJEC-5, LJEC-9)." The task brief says new file `test_humanoid_rig_segments.py`. There is a conflict.
**Assumption made:** Create a new file `tests/core/test_humanoid_rig_segments.py` per the task brief. The NEXT ACTION in the ticket was guidance from Spec Agent using an older plan; the task brief is the authoritative instruction for this run. Existing `test_rig_ratios.py` is NOT modified (LJEC-9-AC1 requires it pass without modification — adding tests there would not break it, but the task brief is explicit about target file).
**Confidence:** High

---

### [M5-LJEC] TEST_DESIGN — `_mesh_str` test placement

**Would have asked:** The task says `tests/core/test_mesh_str.py`. The NEXT ACTION says `test_animated_enemy_classes.py`. The task brief is used as authoritative.
**Assumption made:** New file `tests/core/test_mesh_str.py` per task brief.
**Confidence:** High

---

### [M5-LJEC] TEST_DESIGN — LJEC-6 limb_mesh_helper tests scope

**Would have asked:** The task brief explicitly excludes `test_limb_mesh_helper.py` from the requested deliverables (it lists only 3 target files). The ticket NEXT ACTION mentions `test_limb_mesh_helper.py` for LJEC-6. Which takes precedence?
**Assumption made:** The task brief is the direct instruction for this run and explicitly names 3 target files. LJEC-6 (limb mesh helper) tests are NOT part of this deliverable. They are in scope for a follow-up run.
**Confidence:** High
