# Registry tabs and a fullscreen button

I wanted the asset editor’s registry pane to stop feeling like an infinite scroll of unrelated concerns, and I wanted the GLB preview to go full-bleed without leaving the page. The straightforward split was: **sub-tabs keyed off the same `RunCmd` list as the command dropdown**, and **element fullscreen on the viewer wrapper** so the rest of the chrome stays put.

The agent stack did what multi-agent flows do best: it forced a spec before tests, then let implementation chase failing Vitest. Where it got fiddly wasn’t the React— it was **tooling assumptions**. Vitest 2 + Vite 5 on an older Node blew up with an opaque `crypto.getRandomValues` error; switching to Node 20 (the repo’s `.nvmrc`) made the whole thing boring again. I’m noting that explicitly because “tests fail mysteriously” is the wrong kind of excitement.

On the product side, the registry change surfaces a lesson I keep relearning: **anything persisted in `localStorage` needs a garbage-in test**. One invalid saved tab token shouldn’t land you on the wrong subtree. The fullscreen work is mostly API mocks in jsdom, so I’m comfortable saying the **resize ping after `fullscreenchange`** is the real contract for R3F; actually dragging OrbitControls in CI is still the sort of thing I’d only chase if release policy demanded it.

Net: two small UX wins, one shared tab-style module so we don’t fork the visual language, and another reminder that the pipeline is only as trustworthy as the Node version printed at the top of the test log.
