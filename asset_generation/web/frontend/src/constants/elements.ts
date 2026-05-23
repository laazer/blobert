export type ElementId =
  | "fire"
  | "ice"
  | "poison"
  | "acid"
  | "earth"
  | "forest"
  | "water"
  | "lightning"
  | "physical";

export type ElementToken = {
  name: string;
  hue: string;
  soft: string;
  ink: string;
  glyph?: string;
};

/** Nine element accents — hues/inks from redesign `shared.jsx`; soft as #RRGGBB on studio bg. */
export const ELEMENTS: Record<ElementId, ElementToken> = {
  fire: { name: "Fire", hue: "#ff6b3d", soft: "#331b17", ink: "#ffd0bd", glyph: "🔥" },
  ice: { name: "Ice", hue: "#5dc1ff", soft: "#192936", ink: "#cdebff", glyph: "❄" },
  poison: { name: "Poison", hue: "#b87dff", soft: "#2b203b", ink: "#e8d6ff", glyph: "☣" },
  acid: { name: "Acid", hue: "#9fe830", soft: "#242f15", ink: "#dbf6a8", glyph: "⌬" },
  earth: { name: "Earth", hue: "#c08e5a", soft: "#2c231d", ink: "#ecd6bd", glyph: "◆" },
  forest: { name: "Forest", hue: "#4cb87d", soft: "#162821", ink: "#c9ecd6", glyph: "✤" },
  water: { name: "Water", hue: "#5fb3e0", soft: "#192731", ink: "#cee6f5", glyph: "◐" },
  lightning: { name: "Lightning", hue: "#ffd23d", soft: "#332c17", ink: "#fff0b8", glyph: "⚡" },
  physical: { name: "Physical", hue: "#a0a0b0", soft: "#24242a", ink: "#dcdce4", glyph: "◼" },
};
