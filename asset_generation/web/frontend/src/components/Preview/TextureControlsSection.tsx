import { useAppStore } from "../../store/useAppStore";
import { ZoneTextureBlock } from "./ZoneTextureBlock";

/**
 * @deprecated Tests and legacy call sites: body-zone surface pattern only.
 * Prefer embedding {@link ZoneTextureBlock} under each zone in FeatureMaterialControls.
 */
export function TextureControlsSection({ slug }: { slug: string }) {
  const defs = useAppStore((st) => st.animatedBuildControls[slug] ?? []);
  const bodyTex = defs.filter((d) => d.key.startsWith("feat_body_texture_"));
  const bodyFinishHex = defs.filter((d) => /^feat_body_(finish|hex)$/.test(d.key));
  return <ZoneTextureBlock zone="body" slug={slug} defs={bodyTex} finishHexDefs={bodyFinishHex} />;
}
