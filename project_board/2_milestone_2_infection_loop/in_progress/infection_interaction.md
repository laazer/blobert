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
STATIC_QA

## Revision
6

## Last Updated By
Core Simulation Agent

## Validation Status
- Tests: Run (Passing)
- Static QA: Not Run
- Integration: Not Run

## Blocking Issues
- None

## Escalation Notes
- None

---

# NEXT ACTION

## Next Responsible Agent
Acceptance Criteria Gatekeeper Agent

## Required Input Schema
```json
{
  "notes": "string"
}
```

## Status
Proceed

## Reason
Core Simulation Agent verified that the pure infection loop modules (EnemyStateMachine, MutationInventory, InfectionAbsorbResolver, and EnemyInfection wiring) satisfy all primary + adversarial InfectionInteraction suites in the headless test runner; ticket is ready for acceptance-criteria validation.

