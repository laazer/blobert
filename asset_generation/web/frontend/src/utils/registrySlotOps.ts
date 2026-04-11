/**
 * Pure helpers for building enemy slot ``version_ids`` payloads (MRVC slots API).
 */

/** Minimal row shape for slot eligibility (registry ``versions``). */
export type EnemySlotCandidate = { id: string; draft: boolean; in_use: boolean };

function isEnemySlotEligible(current: string[], v: EnemySlotCandidate): boolean {
  return !v.draft && v.in_use && !current.includes(v.id);
}

/** Append one eligible version: prefer ``preferredVersionId`` when it is slottable; else first manifest order. */
export function nextEnemySlotsAfterAdd(
  current: string[],
  candidates: readonly EnemySlotCandidate[],
  preferredVersionId?: string | null,
): string[] {
  if (preferredVersionId) {
    const pref = candidates.find((v) => v.id === preferredVersionId);
    if (pref && isEnemySlotEligible(current, pref)) {
      return [...current, pref.id];
    }
  }
  const firstAvailable = candidates.find((v) => isEnemySlotEligible(current, v));
  if (!firstAvailable) return current;
  return [...current, firstAvailable.id];
}

export function nextEnemySlotsAfterRemove(current: string[], index: number): string[] {
  const next = [...current];
  next.splice(index, 1);
  return next;
}

/** True when some version can be appended to slots without violating PUT rules (non-draft, in-use, not already listed). */
export function canAddEnemySlot(
  current: string[],
  candidates: readonly EnemySlotCandidate[],
  _preferredVersionId?: string | null,
): boolean {
  return candidates.some((v) => isEnemySlotEligible(current, v));
}

/** Replace the slot at ``slotIndex`` (0-based) with ``versionId``. Appends if ``slotIndex`` ≥ current length. */
export function replaceSlotAssignment(currentIds: readonly string[], slotIndex: number, versionId: string): string[] {
  if (currentIds.length === 0) return [versionId];
  const k = Math.max(0, Math.floor(slotIndex));
  const next = [...currentIds];
  if (k >= next.length) {
    next.push(versionId);
  } else {
    next[k] = versionId;
  }
  return next;
}

/** Append ``versionId`` if not already present (order preserved). */
export function appendSlotIfMissing(currentIds: readonly string[], versionId: string): string[] {
  if (currentIds.includes(versionId)) return [...currentIds];
  return [...currentIds, versionId];
}

/** Duplicate detection for assigned slot ids only; multiple ``""`` placeholders are allowed (R2). */
export function slotListHasDuplicates(ids: readonly string[]): boolean {
  const assigned = ids.filter((id) => id !== "");
  return new Set(assigned).size !== assigned.length;
}
