import type { CSSProperties } from "react";

/** Matches center column Code / Build / Registry tab buttons in `ThreePanelLayout`. */
export function centerPanelTabBtnStyle(active: boolean): CSSProperties {
  return {
    padding: "4px 10px",
    fontSize: 11,
    border: "1px solid #555",
    borderRadius: 3,
    cursor: "pointer",
    background: active ? "#0e639c" : "#3c3c3c",
    color: "#d4d4d4",
  };
}
