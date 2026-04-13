// @vitest-environment jsdom
import { describe, it, expect, afterEach } from "vitest";
import { cleanup, render, screen } from "@testing-library/react";
import type { AnimatedBuildControlDef } from "../../types";
import { ControlRow, FloatControlsTable, FloatTableRow } from "./BuildControlRow";

afterEach(() => {
  cleanup();
});

describe("ControlRow float", () => {
  const def: Extract<AnimatedBuildControlDef, { type: "float" }> = {
    key: "BODY_BASE",
    label: "Body base",
    type: "float",
    min: 0,
    max: 2,
    step: 0.05,
    default: 1,
    unit: "× nominal",
    hint: "Test hint for mesh.",
  };

  it("renders number input without range slider", () => {
    render(<ControlRow def={def} value={1} onChange={() => {}} />);
    expect(document.querySelector('input[type="range"]')).toBeNull();
    expect(document.querySelector('input[type="number"]')).not.toBeNull();
  });

  it("shows unit and hint when provided", () => {
    render(<ControlRow def={def} value={1} onChange={() => {}} />);
    expect(screen.getByText("× nominal")).toBeInTheDocument();
    expect(screen.getByText("Test hint for mesh.")).toBeInTheDocument();
  });
});

describe("FloatControlsTable", () => {
  const def: Extract<AnimatedBuildControlDef, { type: "float" }> = {
    key: "extra_zone_body_spike_size",
    label: "Body spike size",
    type: "float",
    min: 0.25,
    max: 3,
    step: 0.05,
    default: 1,
    unit: "× zone",
    hint: "Scales spikes.",
  };

  it("renders thead and float rows", () => {
    render(
      <FloatControlsTable
        defs={[def]}
        values={{ extra_zone_body_spike_size: 1 }}
        onFloatChange={() => {}}
        isRowDisabled={() => false}
      />,
    );
    expect(screen.getByRole("columnheader", { name: /^Parameter$/i })).toBeInTheDocument();
    expect(screen.getByRole("spinbutton", { name: "Body spike size" })).toBeInTheDocument();
  });
});

describe("FloatTableRow", () => {
  const def: Extract<AnimatedBuildControlDef, { type: "float" }> = {
    key: "BODY_BASE",
    label: "Body base",
    type: "float",
    min: 0,
    max: 2,
    step: 0.05,
    default: 1,
    unit: "× nominal",
    hint: "Table hint line.",
  };

  it("renders a table row with number input and no range", () => {
    render(
      <table>
        <tbody>
          <FloatTableRow def={def} value={1.2} onChange={() => {}} />
        </tbody>
      </table>,
    );
    expect(document.querySelector('input[type="range"]')).toBeNull();
    expect(screen.getByRole("spinbutton", { name: "Body base" })).toBeInTheDocument();
    expect(screen.getByText("Table hint line.")).toBeInTheDocument();
    expect(screen.getByText("× nominal")).toBeInTheDocument();
  });
});
