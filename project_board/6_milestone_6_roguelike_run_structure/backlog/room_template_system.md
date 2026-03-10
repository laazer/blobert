Title:
Build room template system

Description:
Define room categories and author initial templates for each. Categories:
intro (1), combat (3+), mutation_tease (2), fusion_opportunity (1), cooldown (1), boss (1).
Rooms connect via standardized entry/exit door nodes so the layout system can chain them.

Acceptance Criteria:
- Each room is a self-contained .tscn with Entry and Exit Marker3D nodes
- At minimum: 1 intro, 2 combat, 1 mutation_tease, 1 boss room authored
- Rooms load and unload cleanly without memory leaks
- Entry/exit positions are consistent enough for seamless transitions
