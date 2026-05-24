import {
  studioAnimationClipButton,
  studioAnimationPanelRoot,
  studioAnimationPauseButton,
} from "../../styles/studioPreviewStyles";
import { STUDIO_NEUTRAL_ACCENT } from "../../styles/studioTokens";
import { useAppStore } from "../../store/useAppStore";

const ANIMATION_CLIPS = [
  "Idle", "Walk", "Attack", "Hit", "Death",
  "Spawn", "SpecialAttack", "DamageHeavy", "DamageFire",
  "DamageIce", "Stunned", "Celebrate", "Taunt",
];

export type AnimationControlsAppearance = "legacy" | "studio";

export type AnimationControlsProps = {
  appearance?: AnimationControlsAppearance;
  /** Element hue for studio clip / pause buttons (defaults to neutral accent). */
  accentHue?: string;
};

export function AnimationControls({
  appearance = "legacy",
  accentHue = STUDIO_NEUTRAL_ACCENT,
}: AnimationControlsProps = {}) {
  const availableClips = useAppStore((s) => s.availableClips);
  const activeAnimation = useAppStore((s) => s.activeAnimation);
  const setActiveAnimation = useAppStore((s) => s.setActiveAnimation);
  const isAnimationPaused = useAppStore((s) => s.isAnimationPaused);
  const setIsAnimationPaused = useAppStore((s) => s.setIsAnimationPaused);

  const clips = availableClips && availableClips.length > 0 ? availableClips : ANIMATION_CLIPS;
  const isStudio = appearance === "studio";

  return (
    <div
      data-testid="animation-controls"
      style={
        isStudio
          ? studioAnimationPanelRoot
          : {
              background: "#252526",
              padding: "4px 8px",
              display: "flex",
              gap: 4,
              flexWrap: "wrap",
              alignItems: "center",
            }
      }
    >
      <button
        type="button"
        onClick={() => setIsAnimationPaused(!isAnimationPaused)}
        style={
          isStudio
            ? studioAnimationPauseButton(isAnimationPaused, accentHue)
            : {
                background: isAnimationPaused ? "#a12" : "#0e639c",
                color: "#d4d4d4",
                border: "none",
                borderRadius: 3,
                padding: "2px 8px",
                cursor: "pointer",
                fontSize: 11,
              }
        }
      >
        {isAnimationPaused ? "Resume" : "Pause"}
      </button>
      {clips.map((clip) => (
        <button
          key={clip}
          type="button"
          onClick={() => {
            setActiveAnimation(clip);
            setIsAnimationPaused(false);
          }}
          style={
            isStudio
              ? studioAnimationClipButton(activeAnimation === clip, accentHue)
              : {
                  background: activeAnimation === clip ? "#0e639c" : "#3c3c3c",
                  color: "#d4d4d4",
                  border: "none",
                  borderRadius: 3,
                  padding: "2px 8px",
                  cursor: "pointer",
                  fontSize: 11,
                }
          }
        >
          {clip}
        </button>
      ))}
    </div>
  );
}
