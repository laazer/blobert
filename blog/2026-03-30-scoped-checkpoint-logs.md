I finally got tired of one file pretending to be the whole audit trail. `project_board/CHECKPOINTS.md` had grown into a monolith: every autopilot run, every "would have asked the human" assumption, every resume header, all appended in one place. That is great for archaeology and terrible for anything that pulls the repo into an LLM context window. The fix sounds obvious in hindsight: split checkpoint bodies by ticket and run, and keep a tiny index file that only points at them.

The migration itself was deliberately boring. I froze the current log to a dated archive under `project_board/checkpoints/frozen/` before touching the active path, so nothing is lost if a downstream consumer still expects the old shape for a while. The live `CHECKPOINTS.md` is now an index, not a scroll of doom. New detail lives under `project_board/checkpoints/<ticket-id>/<run-id>.md`. The pre-push blog hook prompt was updated so it knows to look at scoped logs plus the index instead of treating one file as the whole story.

The awkward part is not the filesystem layout. It is that `.claude/` is gitignored in this repo, so the skill text that tells agents *how* to write those scoped files (autopilot, continue flows, bugfix) does not ride along in the commit. The commit that landed is the board state, the frozen archive, and the hook string. If you clone fresh, you get the structure; if you want the orchestrator protocol to match, you still need the local skill edits or a policy change on what gets tracked. That split between "workflow contract in git" and "workflow contract in ignored tooling" is the same class of problem as symlinked `agent_context` — obvious once you have been bitten.

Checkpoint index after the cutover (small on purpose):

```markdown
# Checkpoint Index

This file is intentionally small and acts as an index only.
Full checkpoint bodies live under `project_board/checkpoints/`.
```

Path convention for new runs:

```text
project_board/checkpoints/<ticket-id>/<run-id>.md
```

I am not declaring victory on checkpointing forever. The default failure mode is no longer "paste another 400 lines into the same file and hope the model reads the last paragraph."
