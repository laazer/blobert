// @vitest-environment jsdom
import { describe, it, expect, beforeEach, afterEach, vi } from "vitest";
import { render, screen, cleanup } from "@testing-library/react";
import { ZoneTextureBlock } from "../ZoneTextureBlock";
import type { AnimatedBuildControlDef } from "../../../types";
import { useAppStore } from "../../../store/useAppStore";

// Mock the store
vi.mock("../../../store/useAppStore", () => ({
  useAppStore: vi.fn(),
}));

describe("ZoneTextureBlock - Actual DOM Rendering", () => {
  const mockTextureControls: AnimatedBuildControlDef[] = [
    {
      key: "feat_body_texture_mode",
      label: "Body — Texture mode",
      type: "select_str",
      options: ["none", "gradient", "spots", "checkerboard", "stripes", "assets"],
      default: "none",
    },
    {
      key: "feat_body_texture_pattern",
      label: "Body — Pattern color",
      type: "fill_picker",
    },
    {
      key: "feat_body_texture_background",
      label: "Body — Background color",
      type: "fill_picker",
    },
    {
      key: "feat_body_texture_spot_pattern",
      label: "Body — Spot layout",
      type: "select_str",
      options: ["grid", "scatter"],
      default: "grid",
      segmented: true,
    },
    {
      key: "feat_body_texture_spot_density",
      label: "Body — Spot density",
      type: "float",
      min: 0.5,
      max: 5.0,
      step: 0.5,
      default: 1.0,
    },
    {
      key: "feat_body_texture_stripe_width",
      label: "Body — Stripe width",
      type: "float",
      min: 0.1,
      max: 1.0,
      step: 0.05,
      default: 0.2,
    },
    {
      key: "feat_body_texture_stripe_direction",
      label: "Body — Stripe preset",
      type: "select_str",
      options: ["beachball", "doplar", "swirl"],
      default: "beachball",
      segmented: true,
    },
    {
      key: "feat_body_texture_stripe_rot_yaw",
      label: "Body — Stripe yaw",
      type: "float",
      min: -180.0,
      max: 180.0,
      step: 1.0,
      default: 0.0,
      unit: "deg",
    },
    {
      key: "feat_body_texture_stripe_rot_pitch",
      label: "Body — Stripe pitch",
      type: "float",
      min: -180.0,
      max: 180.0,
      step: 1.0,
      default: 0.0,
      unit: "deg",
    },
    {
      key: "feat_body_texture_asset_id",
      label: "Body — Asset texture",
      type: "str",
      default: "",
    },
    {
      key: "feat_body_texture_asset_tile_repeat",
      label: "Body — Tile repeat",
      type: "float",
      min: 0.5,
      max: 4.0,
      step: 0.1,
      default: 1.0,
    },
  ];

  beforeEach(() => {
    // Reset mocks
    vi.clearAllMocks();
  });

  afterEach(() => {
    cleanup();
  });

  it("renders texture mode selector in the DOM", () => {
    const mockStore = {
      animatedBuildOptionValues: { spider: {} },
      setAnimatedBuildOption: vi.fn(),
      applyAnimatedBuildOptionsForSlug: vi.fn(),
    };
    vi.mocked(useAppStore).mockImplementation((selector) => selector(mockStore as any));

    render(
      <ZoneTextureBlock
        zone="body"
        slug="spider"
        defs={mockTextureControls}
      />
    );

    // The texture mode selector is labeled as "Pattern Setting" in the component
    expect(screen.getByText(/Pattern Setting/i)).toBeInTheDocument();
  });

  it("renders pattern and background controls when texture mode is 'stripes'", () => {
    const mockStore = {
      animatedBuildOptionValues: {
        spider: {
          feat_body_texture_mode: "stripes",
        },
      },
      setAnimatedBuildOption: vi.fn(),
      applyAnimatedBuildOptionsForSlug: vi.fn(),
    };
    vi.mocked(useAppStore).mockImplementation((selector) => selector(mockStore as any));

    render(
      <ZoneTextureBlock
        zone="body"
        slug="spider"
        defs={mockTextureControls}
      />
    );

    // Pattern and background controls are rendered with these labels (without zone prefix)
    expect(screen.getByText(/Pattern color/i)).toBeInTheDocument();
    expect(screen.getByText(/Background color/i)).toBeInTheDocument();
  });

  it("does NOT render pattern/background controls when texture mode is 'none'", () => {
    const mockStore = {
      animatedBuildOptionValues: {
        spider: {
          feat_body_texture_mode: "none",
        },
      },
      setAnimatedBuildOption: vi.fn(),
      applyAnimatedBuildOptionsForSlug: vi.fn(),
    };
    vi.mocked(useAppStore).mockImplementation((selector) => selector(mockStore as any));

    render(
      <ZoneTextureBlock
        zone="body"
        slug="spider"
        defs={mockTextureControls}
      />
    );

    // Pattern and background should NOT be rendered when mode is "none"
    expect(screen.queryByText(/Pattern color/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/Background color/i)).not.toBeInTheDocument();
  });

  it("renders spot controls when texture mode is 'spots'", () => {
    const mockStore = {
      animatedBuildOptionValues: {
        spider: {
          feat_body_texture_mode: "spots",
        },
      },
      setAnimatedBuildOption: vi.fn(),
      applyAnimatedBuildOptionsForSlug: vi.fn(),
    };
    vi.mocked(useAppStore).mockImplementation((selector) => selector(mockStore as any));

    render(
      <ZoneTextureBlock
        zone="body"
        slug="spider"
        defs={mockTextureControls}
      />
    );

    // Spot controls should be rendered
    expect(screen.getByText(/Body — Spot layout/i)).toBeInTheDocument();
    expect(screen.getByText(/Body — Spot density/i)).toBeInTheDocument();

    // Stripe controls should NOT be rendered
    expect(screen.queryByText(/Body — Stripe width/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/Body — Stripe yaw/i)).not.toBeInTheDocument();
  });

  it("renders stripe controls when texture mode is 'stripes'", () => {
    const mockStore = {
      animatedBuildOptionValues: {
        spider: {
          feat_body_texture_mode: "stripes",
        },
      },
      setAnimatedBuildOption: vi.fn(),
      applyAnimatedBuildOptionsForSlug: vi.fn(),
    };
    vi.mocked(useAppStore).mockImplementation((selector) => selector(mockStore as any));

    render(
      <ZoneTextureBlock
        zone="body"
        slug="spider"
        defs={mockTextureControls}
      />
    );

    // Stripe controls should be rendered
    expect(screen.getByText(/Body — Stripe width/i)).toBeInTheDocument();
    expect(screen.getByText(/Body — Stripe preset/i)).toBeInTheDocument();
    expect(screen.getByText(/Body — Stripe yaw/i)).toBeInTheDocument();
    expect(screen.getByText(/Body — Stripe pitch/i)).toBeInTheDocument();

    // Spot controls should NOT be rendered
    expect(screen.queryByText(/Body — Spot layout/i)).not.toBeInTheDocument();
  });

  it("does NOT render pattern-specific controls when texture mode is 'none'", () => {
    const mockStore = {
      animatedBuildOptionValues: {
        spider: {
          feat_body_texture_mode: "none",
        },
      },
      setAnimatedBuildOption: vi.fn(),
      applyAnimatedBuildOptionsForSlug: vi.fn(),
    };
    vi.mocked(useAppStore).mockImplementation((selector) => selector(mockStore as any));

    render(
      <ZoneTextureBlock
        zone="body"
        slug="spider"
        defs={mockTextureControls}
      />
    );

    // No pattern-specific controls should be rendered
    expect(screen.queryByText(/Body — Spot layout/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/Body — Spot density/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/Body — Stripe width/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/Body — Stripe preset/i)).not.toBeInTheDocument();
  });
});
