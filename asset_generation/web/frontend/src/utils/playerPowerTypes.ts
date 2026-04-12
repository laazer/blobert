/** Client-side power type sections for the player registry tab (stored in localStorage). */

export type PlayerPowerType = {
  id: string;
  label: string;
};

const LS_TYPES_KEY = "blobert.player.power_types";
const LS_SLOTS_PREFIX = "blobert.player.pt_slots.";

export const DEFAULT_POWER_TYPES: PlayerPowerType[] = [{ id: "default", label: "Default" }];

/** Generate a stable unique id for a new power type. */
export function generatePowerTypeId(): string {
  return `pt_${Date.now().toString(36)}_${Math.random().toString(36).slice(2, 6)}`;
}

export function loadPlayerPowerTypes(): PlayerPowerType[] {
  if (typeof localStorage === "undefined") return DEFAULT_POWER_TYPES;
  try {
    const raw = localStorage.getItem(LS_TYPES_KEY);
    if (!raw) return DEFAULT_POWER_TYPES;
    const parsed = JSON.parse(raw) as unknown;
    if (!Array.isArray(parsed) || parsed.length === 0) return DEFAULT_POWER_TYPES;
    const valid = parsed.filter(
      (item): item is PlayerPowerType =>
        typeof item === "object" &&
        item !== null &&
        typeof (item as PlayerPowerType).id === "string" &&
        (item as PlayerPowerType).id.trim() !== "" &&
        typeof (item as PlayerPowerType).label === "string",
    );
    return valid.length > 0 ? valid : DEFAULT_POWER_TYPES;
  } catch {
    return DEFAULT_POWER_TYPES;
  }
}

export function savePlayerPowerTypes(types: PlayerPowerType[]): void {
  if (typeof localStorage === "undefined") return;
  try {
    localStorage.setItem(LS_TYPES_KEY, JSON.stringify(types));
  } catch {
    /* quota / private mode — ignore */
  }
}

export function loadPowerTypeSlots(ptId: string): string[] {
  if (typeof localStorage === "undefined") return [];
  try {
    const raw = localStorage.getItem(`${LS_SLOTS_PREFIX}${ptId}`);
    if (!raw) return [];
    const parsed = JSON.parse(raw) as unknown;
    if (!Array.isArray(parsed)) return [];
    return parsed.filter((s): s is string => typeof s === "string");
  } catch {
    return [];
  }
}

export function savePowerTypeSlots(ptId: string, slots: string[]): void {
  if (typeof localStorage === "undefined") return;
  try {
    localStorage.setItem(`${LS_SLOTS_PREFIX}${ptId}`, JSON.stringify(slots));
  } catch {
    /* quota / private mode — ignore */
  }
}

/** Pure: returns a new array with the power type appended. */
export function addPowerType(types: PlayerPowerType[], label: string): PlayerPowerType[] {
  return [...types, { id: generatePowerTypeId(), label: label.trim() || "New power type" }];
}

/** Pure: returns a new array with the matching id's label replaced. No-op if id not found. */
export function renamePowerType(types: PlayerPowerType[], id: string, label: string): PlayerPowerType[] {
  return types.map((pt) => (pt.id === id ? { ...pt, label: label.trim() || pt.label } : pt));
}

/** Pure: removes the entry with the given id. Returns original array unchanged if only one entry. */
export function removePowerType(types: PlayerPowerType[], id: string): PlayerPowerType[] {
  if (types.length <= 1) return types;
  return types.filter((pt) => pt.id !== id);
}
