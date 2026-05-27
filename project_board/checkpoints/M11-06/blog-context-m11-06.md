# Blog Context Capsule — M11-06

- **Ticket:** M11-06 (AttackDatabase Integration)
- **Goal:** Create AttackDatabase autoload and integrate attack pipeline into PlayerController3D
- **Outcome:** COMPLETE
- **Git commits:** `9b950dc`
- **Checkpoint log:** `project_board/checkpoints/M11-06/`
- **Rework/surprises:**
  - EC-20 test setup bug: Test Breaker misunderstood MutationSlotManager.fill_next_available fill order, wrote test that left both slots empty instead of filling slot B. Orchestrator fixed by adding dummy fill before target fill.
  - Every subagent produced handoff artifacts with incorrect schema (wrong field names, missing required keys). Orchestrator manually fixed all 5 handoff YAML files and 4 todos JSON files.
  - Implementation agent correctly identified the EC-20 failure as a test bug but didn't fix it — orchestrator patched the test post-implementation.
  - PlayerController3D hit exactly 900 lines (the gd-organization limit), signaling future refactoring need.
