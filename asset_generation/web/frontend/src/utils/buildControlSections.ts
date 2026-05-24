import type { AnimatedBuildControlDef } from "../types";

export type BuildSectionId =
  | "body"
  | "eyes"
  | "mouth"
  | "tail"
  | "pattern"
  | "rig"
  | "advanced";

export const BUILD_SECTION_ORDER: readonly BuildSectionId[] = [
  "body",
  "eyes",
  "mouth",
  "tail",
  "pattern",
  "rig",
  "advanced",
] as const;

export const BUILD_SECTION_LABEL: Record<BuildSectionId, string> = {
  body: "Body",
  eyes: "Eyes",
  mouth: "Mouth",
  tail: "Tail",
  pattern: "Pattern parameters",
  rig: "Rig",
  advanced: "Advanced",
};

/** Default expanded state for v2 Build inspector sections. */
export const BUILD_SECTION_DEFAULT_OPEN: Record<BuildSectionId, boolean> = {
  body: true,
  eyes: true,
  mouth: false,
  tail: false,
  pattern: true,
  rig: false,
  advanced: false,
};

export function classifyBuildControlSection(
  key: string,
  type: AnimatedBuildControlDef["type"],
): BuildSectionId {
  if (key.startsWith("RIG_")) return "rig";
  const kl = key.toLowerCase();
  const ku = key.toUpperCase();

  if (kl === "placement_seed" || kl === "peripheral_eyes") return "advanced";
  if (kl.startsWith("eye_") || kl.startsWith("pupil_") || ku.includes("EYE")) return "eyes";
  if (kl.startsWith("mouth_")) return "mouth";
  if (kl.startsWith("tail_")) return "tail";
  if (kl === "body_type") return "body";

  if (type === "float") {
    if (
      ku.includes("BODY") ||
      ku.includes("TORSO") ||
      ku.includes("CENTER_Z") ||
      (ku.includes("SCALE_Y") && !ku.includes("LIMB")) ||
      (ku.includes("SCALE_Z") && !ku.includes("LIMB")) ||
      ku.endsWith("_VARIANCE")
    ) {
      if (!ku.includes("EYE")) return "body";
    }
    return "pattern";
  }

  if (kl === "body_type" || ku.includes("BODY")) return "body";
  return "advanced";
}

export function partitionBuildControls(
  defs: readonly AnimatedBuildControlDef[],
): Record<BuildSectionId, AnimatedBuildControlDef[]> {
  const out: Record<BuildSectionId, AnimatedBuildControlDef[]> = {
    body: [],
    eyes: [],
    mouth: [],
    tail: [],
    pattern: [],
    rig: [],
    advanced: [],
  };
  for (const def of defs) {
    out[classifyBuildControlSection(def.key, def.type)].push(def);
  }
  return out;
}

export function pupilControlDefs(
  eyesDefs: readonly AnimatedBuildControlDef[],
): AnimatedBuildControlDef[] {
  return eyesDefs.filter((d) => d.key.toLowerCase().startsWith("pupil_"));
}

export function eyesDefsWithoutPupil(
  eyesDefs: readonly AnimatedBuildControlDef[],
): AnimatedBuildControlDef[] {
  return eyesDefs.filter((d) => !d.key.toLowerCase().startsWith("pupil_"));
}

function readStr(values: Readonly<Record<string, unknown>>, key: string, fallback: string): string {
  const v = values[key];
  return typeof v === "string" ? v : fallback;
}

function readNum(values: Readonly<Record<string, unknown>>, key: string, fallback: number): number {
  const v = values[key];
  return typeof v === "number" && Number.isFinite(v) ? v : fallback;
}

function readBool(values: Readonly<Record<string, unknown>>, key: string, fallback: boolean): boolean {
  const v = values[key];
  return typeof v === "boolean" ? v : fallback;
}

function fmt(n: number): string {
  if (Number.isInteger(n)) return String(n);
  return n.toFixed(2).replace(/\.?0+$/, "");
}

/** One-line summary for a collapsed section header (design mock). */
export function summarizeBuildSection(
  sectionId: BuildSectionId,
  defs: readonly AnimatedBuildControlDef[],
  values: Readonly<Record<string, unknown>>,
): string {
  if (defs.length === 0) return "";

  switch (sectionId) {
    case "body": {
      const bt = readStr(values, "body_type", "default");
      const y = defs.find((d) => d.key.toUpperCase().includes("SCALE_Y") && d.type === "float");
      const z = defs.find((d) => d.key.toUpperCase().includes("SCALE_Z") && d.type === "float");
      if (y?.type === "float" && z?.type === "float") {
        const yv = readNum(values, y.key, y.default);
        const zv = readNum(values, z.key, z.default);
        return `${bt} · scale ${fmt(yv)}/${fmt(zv)}`;
      }
      return bt;
    }
    case "eyes": {
      const count = readNum(values, "eye_count", 2);
      const shape = readStr(values, "eye_shape", "circle");
      const dist = readStr(values, "eye_distribution", "uniform");
      const pupilOn = readBool(values, "pupil_enabled", false);
      const base = `${count} · ${shape} · ${dist}`;
      return pupilOn ? `${base} · pupil` : base;
    }
    case "mouth": {
      const on = readBool(values, "mouth_enabled", false);
      if (!on) return "off";
      return readStr(values, "mouth_shape", "off");
    }
    case "tail": {
      const on = readBool(values, "tail_enabled", false);
      if (!on) return "off";
      const shape = readStr(values, "tail_shape", "");
      return shape || "on";
    }
    case "rig": {
      const headX = defs.find((d) => d.key === "RIG_HEAD_ROT_X");
      if (headX?.type === "float") {
        const x = readNum(values, "RIG_HEAD_ROT_X", headX.default);
        const y = readNum(values, "RIG_HEAD_ROT_Y", 0);
        const z = readNum(values, "RIG_HEAD_ROT_Z", 0);
        return `head ${fmt(x)}° / ${fmt(y)}° / ${fmt(z)}°`;
      }
      return `${defs.length} controls`;
    }
    case "pattern":
      return `${defs.length} sliders`;
    case "advanced":
      return defs.map((d) => d.label).slice(0, 2).join(" · ");
    default:
      return "";
  }
}
