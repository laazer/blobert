# TICKET: orbital_aim_soft_assist

Title: Orbital aim — optional soft aim assist toward valid targets

## Description

Implement an optional assist that applies a slight angular pull toward a valid target when θ is within a configurable angular threshold. Strength scales with proximity. Player input always overrides assist; assist must be fully toggleable and tunable.

## Acceptance Criteria

- **AC-8.1** When θ is within exported threshold of a valid target angle, apply bounded pull toward that target.
- **AC-8.2** Assist strength scales with how close θ is to the target angle (document curve: linear or smoothstep — match implementation).
- **AC-8.3** Any intentional snap or rotation input overrides assist for that frame (assist does not block aiming away).
- **AC-8.4** Assist can be disabled entirely and all parameters (strength, threshold, max pull per frame if used) are exported or config-driven.
- **AC-12.5** Aim assist strength and effective “radius” (threshold) exported; toggle exposed.
- `run_tests.sh` exits 0 (unit-style tests with mocked target angles if no entities yet).

## Dependencies

- `orbital_aim_core_representation`
- `orbital_aim_input_integration_edge_cases` — correct precedence with assist last or documented merge order

## Notes

- Define “valid target” minimally for first slice (e.g. nearest enemy bearing in XZ plane) or stub provider interface if gameplay hooks are not ready.
