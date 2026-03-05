# Infection interaction

**Epic:** Milestone 2 – Infection Loop  
**Status:** In Progress

---

## Description

Implement the infection interaction: when the slime (or chunk) interacts with a weakened enemy, the enemy becomes infected and the player can absorb to gain a mutation. One mutation minimum for this milestone.

## Acceptance criteria

- [ ] Weakened enemy can be infected via defined interaction (e.g. chunk contact, key press)
- [ ] Infected state is distinct; player can absorb to gain mutation
- [ ] At least one mutation is granted and usable after absorb
- [ ] No softlock or undefined state when infecting/absorbing
- [ ] Infection interaction is human-playable in-editor: weakened/enemy states, infection, and absorb feedback are visually clear and discoverable without debug overlays

---

# WORKFLOW STATE (DO NOT FREEFORM EDIT)

## Stage
COMPLETE

## Revision
8

## Last Updated By
Human

## Validation Status
- Tests: Run (Passing) — primary + adversarial InfectionInteraction suites cover AC 1–4 (infection trigger, infected state + absorb, mutation grant/usage, and softlock/undefined-state protections).
- Static QA: Not Run
- Integration: Run (Passing) — human manually verified in-editor that weakened/enemy states, infection, and absorb feedback are visually clear and discoverable without debug overlays.

## Blocking Issues
- None

## Escalation Notes
- None

---

# NEXT ACTION

## Next Responsible Agent
Human

## Required Input Schema
```json
{
  "notes": "string"
}
```

## Status
Proceed

## Reason
Human verified in-editor that all infection interaction acceptance criteria, including visual clarity and discoverability without debug overlays, are satisfied; ticket is marked COMPLETE.

