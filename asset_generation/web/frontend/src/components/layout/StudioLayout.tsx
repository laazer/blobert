import { studioLayoutRootStyle } from "../../styles/studioTokens";
import { EnemyLibrary } from "../studio/EnemyLibrary";
import { StudioInspector } from "../studio/StudioInspector";
import { StudioPreviewColumn } from "../studio/StudioPreviewColumn";
import { StudioTopBar } from "../studio/StudioTopBar";

export function StudioLayout() {
  return (
    <div data-testid="studio-layout" style={studioLayoutRootStyle}>
      <StudioTopBar />
      <EnemyLibrary />
      <StudioPreviewColumn />
      <StudioInspector />
    </div>
  );
}
