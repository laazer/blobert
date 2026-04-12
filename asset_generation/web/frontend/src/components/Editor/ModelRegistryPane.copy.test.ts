import { describe, expect, it } from "vitest";
import {
  DRAFT_DELETE_CONFIRM_COPY,
  IN_USE_DELETE_CONFIRM_COPY,
  ENEMY_EMPTY_SLOTS_COPY,
  LOAD_EXISTING_EMPTY_COPY,
} from "./ModelRegistryPane";

describe("ModelRegistryPane UX copy contracts", () => {
  it("documents fallback behavior when a family has zero slots", () => {
    expect(ENEMY_EMPTY_SLOTS_COPY.toLowerCase()).toContain("falls back");
    expect(ENEMY_EMPTY_SLOTS_COPY.toLowerCase()).toContain("legacy default path");
  });

  it("documents explicit empty-state guidance for load-existing picker", () => {
    expect(LOAD_EXISTING_EMPTY_COPY.toLowerCase()).toContain("no draft or in-use registry models available");
  });

  it("documents irreversible draft-delete confirmation requirements", () => {
    expect(DRAFT_DELETE_CONFIRM_COPY.toLowerCase()).toContain("confirm");
    expect(DRAFT_DELETE_CONFIRM_COPY.toLowerCase()).toContain("irreversible");
    expect(DRAFT_DELETE_CONFIRM_COPY.toLowerCase()).toContain("registry");
  });

  it("documents in-use delete guardrails and rejection reasons", () => {
    expect(IN_USE_DELETE_CONFIRM_COPY.toLowerCase()).toContain("in-use");
    expect(IN_USE_DELETE_CONFIRM_COPY.toLowerCase()).toContain("spawn");
    expect(IN_USE_DELETE_CONFIRM_COPY.toLowerCase()).toContain("may be rejected");
  });
});
