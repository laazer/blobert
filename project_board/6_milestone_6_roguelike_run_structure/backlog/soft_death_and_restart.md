Title:
Implement soft death state and run restart

Description:
When the player reaches 0 HP, trigger a soft death: brief pause, slime dissolves animation,
then seamless reset back to the entry room with a fresh run layout. No harsh game over screen.
Tone should feel like "the lab resets the experiment."

Acceptance Criteria:
- Death does not hard-crash or hang
- Brief visual feedback on death (dissolve or fade)
- Run resets within 2 seconds of death trigger
- Mutation slots are empty on restart
- Player position and HP are fully reset
- New room layout is generated on each restart
