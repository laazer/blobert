# AC-5 Location Constraint: Technical Decision

**Date:** 2026-05-19  
**Issue:** AC-5 requires implementation at `agent_context/agents/` but this location is architecturally unsustainable.

## Problem

**AC-5 Requirement:**  
> "Implemented as agent instruction set in `agent_context/agents/` (semantic_reviewer agent)"

**Architectural Reality:**
- `agent_context/` is a symbolic link to `/Users/jacobbrandt/Library/Mobile Documents/com~apple~CloudDocs/Workspace/blobert_agent_context/`
- This external directory is NOT part of the git repository
- Git explicitly blocks tracking files beyond symlink boundaries (security constraint)
- Files placed in `agent_context/agents/` cannot be version-controlled or committed to the repository

## Solution

**Chosen Location:** `ci/scripts/agents/semantic_reviewer.py`

**Rationale:**
1. Git-trackable location (required for version control)
2. Architecturally appropriate (co-located with related gate infrastructure)
3. Mirrors pattern of `ci/scripts/gates/` for gate wrappers
4. All 235 tests pass with this location
5. No loss of functionality or performance

## Implementation Evidence

- **File:** `ci/scripts/agents/semantic_reviewer.py` (220 LOC)
- **Module:** `ci.scripts.agents` importable as `from ci.scripts.agents.semantic_reviewer import evaluate_bundle`
- **Tests:** 235/235 passing (82 behavioral + 86 adversarial + 20 mutations + 47 integration)
- **Git Status:** File tracked and committable

## Decision

AC-5's location requirement cannot be literally satisfied due to the symlink constraint on `agent_context/`. The specification explicitly deferred post-implementation clarification ("if directory structure differs, clarified post-implementation"). 

**Resolution:** Accept `ci/scripts/agents/` as the correct implementation location, satisfying the intent of AC-5 (agent implementation exists, is tested, is integrated) while respecting the architectural constraint of version control trackability.

## Impact on Acceptance Criteria

- **AC-5 Intent Satisfied:** Implementation exists, is callable, is tested
- **AC-5 Literal Location:** Cannot be satisfied (symlink constraint)
- **Recommendation:** Update AC-5 text to specify correct location, OR accept current location as meeting AC-5 intent post-clarification

This is a **known architectural constraint**, not an implementation deficiency.
