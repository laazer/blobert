# M25-02b — Integrate Universal Color Picker

**Run:** 2026-04-18 autopilot (single ticket)

## Summary

- Added `lockMode` to `ColorPickerUniversal` so embedded rows can hide mode tabs (single / gradient / image).
- `BuildControlRow` hex + texture color `str` defs now use `ColorPickerUniversal` in `lockMode="single"` with **Paste color** preserved (`readHexFromClipboard`).
- `ZoneTextureBlock` replaces separate gradient A/B/direction `ControlRow`s with one `ColorPickerUniversal` in `lockMode="gradient"` wired to `feat_{zone}_texture_grad_color_a|b` and `feat_{zone}_texture_grad_direction`.
- Updated `BuildControls.texture.test.tsx` to assert gradient via “From Color” / “To Color” / `role="group"` name `Gradient direction`.

## Image mode (AC)

BuildControls has no client-side custom texture **file** row in this branch (M25-03 upload UI not present). **Image** mode remains available on `ColorPickerUniversal` (`lockMode="image"`) and is covered by `ColorPickerUniversal` + `ImageMode` tests; wiring to a future upload row is ticket 02c / M25-03 follow-up.

## Confidence

- High: single + gradient integration, Vitest full frontend green.
