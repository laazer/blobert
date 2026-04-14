# TICKET: orbital_aim_core_representation

Title: Orbital aim — core θ model, ring semantics, direction vector, idle stability

## Description

Introduce the authoritative aim state for the 3D player: a single angle θ, normalized for all readers, plus a derived horizontal (or gameplay-plane) unit direction used by future systems (projectiles, abilities). Model aim as a point on a fixed-radius ring for logic; keep visual radius separate for presentation.

## Acceptance Criteria

- **AC-1.1** Aim is represented as a single angle θ (document whether degrees at API boundary or radians internally; conversions are explicit and consistent).
- **AC-1.2** θ is always normalized to 0° ≤ θ < 360° (or equivalent radian range \[0, 2π)).
- **AC-1.3** A unit direction vector is derived from θ and is the single source for gameplay-facing aim (document axis convention, e.g. +X = 0° in XZ plane).
- **AC-2.1** Design/docs in code or ticket notes: aim is a point on a fixed-radius ring around the player.
- **AC-2.2** Gameplay ring radius is constant for simulation; visual ring radius is configurable independently.
- **AC-2.3** When θ changes (from any later ticket’s input), aim direction updates immediately and continuously from the new θ.
- **AC-7.1** With no active aim input (once input layer exists), θ does not drift frame-to-frame.
- **AC-7.2** No decay, auto-centering, or hidden forces applied to θ when idle.
- **AC-12.x (partial)** Export gameplay ring radius, visual ring radius (if visuals not in this ticket, stub exports on the component that will own them), and any normalization/tolerance constants needed for tests.
- `run_tests.sh` exits 0 (add or extend Godot tests for normalization and direction consistency if a harness exists).

## Dependencies

- M1 — `PlayerController3D` / 3D sandbox as integration point

## Notes

- Prefer a small dedicated module or inner class for θ + `Vector3` derivation to keep input tickets from duplicating math.
