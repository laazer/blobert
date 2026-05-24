import type { ElementId } from "../../constants/elements";
import { ELEMENTS } from "../../constants/elements";
import { StudioFamilyGlyph } from "./StudioFamilyGlyph";

type Props = {
  familyId: string;
  versionId: string;
  elementId: ElementId;
  title?: string;
};

/** Version list icon: family glyph from redesign, tinted by the version's element tag. */
export function StudioVersionThumb({ familyId, versionId, elementId, title }: Props) {
  const el = ELEMENTS[elementId];

  return (
    <div title={title} data-testid={`studio-version-thumb-${versionId}`}>
      <StudioFamilyGlyph
        familyId={familyId}
        elementGlyph={el.glyph}
        hue={el.hue}
        soft={el.soft}
        ink={el.ink}
        size={32}
      />
    </div>
  );
}
