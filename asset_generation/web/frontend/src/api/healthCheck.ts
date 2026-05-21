import { getHealth } from "../api-client";

export type { HealthResponse } from "../schemas";

/** Validated GET /api/health (M902-25). */
export const fetchHealth = getHealth;
