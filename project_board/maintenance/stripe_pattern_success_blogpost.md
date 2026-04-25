## Title

From Warped UVs to Reliable Stripes: Fixing Distortion, Rotation, and Viewer Parity in Our Mesh Texturing Pipeline

## Problem

We hit a frustrating quality gap in our stripe texturing pipeline: stripes looked correct in some assets and totally wrong in others. Depending on orientation and export path, we saw visible distortion, unexpected rotation, and mismatches between generated assets and the web viewer. The issue was especially painful because it undercut confidence in iteration speed; artists and engineers could not trust that what they previewed would match what shipped.

At a glance, this looked like "just a shader quirk." In practice, it was a cross-stage pipeline problem touching coordinate spaces, projection assumptions, and export behavior. The breakthrough came when we stopped treating each symptom independently and rebuilt the mental model end-to-end: UV generation, stripe direction math, object orientation, and final baked output.

## Root Cause

The core failure mode was inconsistent coordinate-space reasoning.

First, we had UV-space rotation bugs. Stripe orientation logic assumed a stable interpretation of U/V axes, but mesh orientation and projection choices made those assumptions invalid in edge cases. Rotations that should have been orthogonal were effectively compounded or mirrored, producing skewed or twisted stripe fields.

Second, our previous approach mixed legacy behavior and newer stripe logic without a clean boundary. That made it easy for fixes in one pattern family to regress another. Beachball/swirl and doplar behaviors had diverged conceptually, but parts of the implementation still treated them as variants of the same mechanism.

Third, preview/export parity was incomplete. Even when in-editor output looked right, exported artifacts for the web viewer could differ because shading-time behavior and delivered textures were not always equivalent representations.

## What Changed

We made five concrete changes that turned this from a bugfix into a durable pipeline upgrade:

1. **Projection-based refactor of stripe generation**  
   We replaced brittle UV-rotation assumptions with projection-centric logic that computes stripe behavior from explicit geometric intent. Instead of rotating UVs and hoping orientation follows, we now derive stripe mapping through a clearer projection model, reducing ambiguity across mesh poses.

2. **Object-space doplar stripes**  
   Doplar moved to object-space logic so stripe direction remains stable relative to the model, not accidental UV layout artifacts. This eliminated the most visible rotation drift and made results predictable under transforms that previously produced distortions.

3. **Export-time bake for web viewer parity**  
   We introduced an export-time bake step so the web viewer consumes textures that faithfully represent runtime stripe results. That closed the "looks right locally, wrong in viewer" loop and made QA verification straightforward across environments.

4. **Legacy behavior preservation for beachball/swirl**  
   We explicitly restored legacy beachball/swirl behavior, rather than forcing those modes through the new doplar path. This gave us the best of both worlds: stability for established looks and modernized logic where needed.

5. **Logic separation and contract hardening**  
   We tightened the boundary between stripe modes and codified expected output behavior at integration points. That reduced cross-mode side effects and made future changes safer.

## Validation

We treated validation as a first-class deliverable, not an afterthought.

- **Targeted unit tests** covered stripe texture generation invariants and orientation behavior under representative rotation/projection inputs.
- **Integration tests** exercised material assembly and export hooks, specifically asserting parity between generated output and viewer-facing artifacts.
- **Regression checks** ensured beachball/swirl preserved legacy expectations while doplar followed the new object-space rules.
- **Visual sanity passes** were used as final confirmation, but only after automated checks established behavioral guarantees.

The key result: distortion and rotation issues were eliminated for doplar in tested scenarios, web viewer parity was restored through baking, and legacy modes remained stable.

## Lessons

- **Coordinate-space bugs are architecture bugs in disguise.**  
  If UV-space and object-space responsibilities are fuzzy, small fixes will not stick.

- **Refactors should separate behavior families, not just rewrite formulas.**  
  Keeping doplar and legacy modes loosely coupled prevents accidental regressions.

- **Parity must be designed, not assumed.**  
  Export-time baking was essential because runtime evaluation and delivered texture consumption are different systems.

- **Testing strategy matters more than test volume.**  
  A compact suite that encodes invariants, parity, and regressions beats broad but shallow coverage.

- **Visual verification is necessary but insufficient.**  
  Human checks catch aesthetics; automated tests protect correctness over time.

## What’s Next

Next steps are about scaling confidence:

- Expand orientation test matrices across more mesh classes and extreme transforms.
- Add stricter contract tests around export metadata and bake outputs.
- Profile bake performance and cache behavior for larger batch exports.
- Continue reducing mode coupling so future stripe variants can be added without reopening legacy risks.

This fix was a strong reminder that the fastest path to visual reliability is technical clarity: explicit spaces, explicit contracts, and tests that lock in intent.
