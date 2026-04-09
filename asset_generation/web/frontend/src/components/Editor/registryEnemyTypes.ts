import type { DeleteEnemyVersionRequest } from "../../api/client";

export type EnemyDeletePlan = {
  confirmMessage: string;
  request: DeleteEnemyVersionRequest;
};
