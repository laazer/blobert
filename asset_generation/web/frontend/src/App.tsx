import { useEffect } from "react";
import { StudioLayout } from "./components/layout/StudioLayout";
import { ThreePanelLayout } from "./components/layout/ThreePanelLayout";
import { useAppStore } from "./store/useAppStore";
import { isStudioLayoutEnabled } from "./utils/studioLayoutFlag";

export default function App() {
  const loadAnimatedEnemyMeta = useAppStore((s) => s.loadAnimatedEnemyMeta);
  useEffect(() => {
    loadAnimatedEnemyMeta();
  }, [loadAnimatedEnemyMeta]);

  return isStudioLayoutEnabled() ? <StudioLayout /> : <ThreePanelLayout />;
}
