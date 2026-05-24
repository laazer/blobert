import { ELEMENTS, type ElementId } from "../../constants/elements";
import { elementTagChipStyle } from "../../utils/studioVersionUi";

function isElementTag(tag: string): tag is ElementId {
  return tag in ELEMENTS;
}

type Props = {
  tags: readonly string[];
};

export function StudioTopBarBreadcrumbTags({ tags }: Props) {
  if (tags.length === 0) return null;

  return (
    <span
      data-testid="studio-top-bar-tags"
      style={{ display: "inline-flex", flexWrap: "wrap", gap: 4, alignItems: "center", marginLeft: 4 }}
    >
      {tags.map((tag) => {
        const elStyle = isElementTag(tag) ? elementTagChipStyle(tag) : null;
        return (
          <span
            key={tag}
            data-testid={`studio-top-bar-tag-${tag}`}
            style={{
              display: "inline-flex",
              alignItems: "center",
              padding: "2px 8px",
              borderRadius: 999,
              fontSize: 10,
              fontWeight: 600,
              ...(elStyle ?? {
                background: "rgba(255,255,255,0.04)",
                color: "#bababf",
                border: "1px solid rgba(255,255,255,0.08)",
              }),
            }}
          >
            {tag}
          </span>
        );
      })}
    </span>
  );
}
