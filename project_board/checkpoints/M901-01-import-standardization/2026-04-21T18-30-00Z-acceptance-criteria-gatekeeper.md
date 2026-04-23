### [M901-01-import-standardization] INTEGRATION — AC gate vs folder rule
**Would have asked:** Should Stage be set to `COMPLETE` per user directive when the ticket file still lives under `ready/` (workflow enforcement requires `COMPLETE` tickets under `project_board/**/done/`)?
**Assumption made:** Do not set `COMPLETE` until the ticket is moved to the milestone `done/` folder; keep Stage at `INTEGRATION` with all AC evidence documented in Validation Status and route `NEXT ACTION` to Human for folder move + formal closure.
**Confidence:** High
