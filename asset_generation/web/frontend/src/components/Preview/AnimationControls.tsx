import { useAppStore } from "../../store/useAppStore";

const ANIMATION_CLIPS = [
  "Idle", "Walk", "Attack", "Hit", "Death",
  "Spawn", "SpecialAttack", "DamageHeavy", "DamageFire",
  "DamageIce", "Stunned", "Celebrate", "Taunt",
];

export function AnimationControls() {
  const availableClips = useAppStore((s) => s.availableClips);
  const activeAnimation = useAppStore((s) => s.activeAnimation);
  const setActiveAnimation = useAppStore((s) => s.setActiveAnimation);
  const isAnimationPaused = useAppStore((s) => s.isAnimationPaused);
  const setIsAnimationPaused = useAppStore((s) => s.setIsAnimationPaused);

  const clips = availableClips && availableClips.length > 0 ? availableClips : ANIMATION_CLIPS;

  return (
    <div style={{
      background: "#252526",
      padding: "4px 8px",
      display: "flex",
      gap: 4,
      flexWrap: "wrap",
      alignItems: "center",
    }}>
      <button
        onClick={() => setIsAnimationPaused(!isAnimationPaused)}
        style={{
          background: isAnimationPaused ? "#a12" : "#0e639c",
          color: "#d4d4d4",
          border: "none",
          borderRadius: 3,
          padding: "2px 8px",
          cursor: "pointer",
          fontSize: 11,
        }}
      >
        {isAnimationPaused ? "Resume" : "Pause"}
      </button>
      {clips.map((clip) => (
        <button
          key={clip}
          onClick={() => {
            setActiveAnimation(clip);
            setIsAnimationPaused(false);
          }}
          style={{
            background: activeAnimation === clip ? "#0e639c" : "#3c3c3c",
            color: "#d4d4d4",
            border: "none",
            borderRadius: 3,
            padding: "2px 8px",
            cursor: "pointer",
            fontSize: 11,
          }}
        >
          {clip}
        </button>
      ))}
    </div>
  );
}
