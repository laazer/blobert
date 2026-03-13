Title:
Implement procedural room chaining

Description:
System that assembles a run's room sequence from the template pool each time a run starts.
Fixed structure: intro → N combat rooms → mutation tease → fusion room → boss.
Combat rooms and tease rooms drawn randomly from their pools. Seed logged for debugging.

Acceptance Criteria:
- Run layout generated fresh each run start
- Sequence always follows fixed category order
- No room repeated in a single run
- RNG seed printed to console for reproducibility during testing
- Transitions between rooms feel seamless (no visible load pop)
