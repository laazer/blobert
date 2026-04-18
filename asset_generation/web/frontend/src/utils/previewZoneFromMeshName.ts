/**
 * Map GLB mesh object names to coarse material zones (feat_* body/head/limbs/joints/extra).
 * Heuristic only — used for client-side preview overlays.
 */
export function previewZoneFromMeshName(meshName: string): string | null {
  const n = meshName.toLowerCase();
  if (/(joint|hinge|socket)/.test(n)) return "joints";
  if (/(leg|arm|limb|stalk|segment|claw|foot|thigh)/.test(n)) return "limbs";
  if (/(head|face|eye|sclera|pupil|cheek|mouth|jaw)/.test(n)) return "head";
  if (/(tail|horn|wing|spike)/.test(n)) return "extra";
  if (/(body|torso|abdomen|carapace|shell|blob|slime|core)/.test(n)) return "body";
  return null;
}
