/**
 * Pure helpers for building enemy slot ``version_ids`` payloads (MRVC slots API).
 */

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

export function slotListHasDuplicates(ids: readonly string[]): boolean {
  return new Set(ids).size !== ids.length;
}
