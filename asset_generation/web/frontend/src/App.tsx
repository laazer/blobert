import { useEffect } from "react";
import { ThreePanelLayout } from "./components/layout/ThreePanelLayout";
import { useAppStore } from "./store/useAppStore";

export default function App() {
  const loadAnimatedEnemyMeta = useAppStore((s) => s.loadAnimatedEnemyMeta);
  useEffect(() => {
    loadAnimatedEnemyMeta();
  }, [loadAnimatedEnemyMeta]);

  return <ThreePanelLayout />;
}
