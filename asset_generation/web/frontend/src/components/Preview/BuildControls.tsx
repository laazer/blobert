import { useEffect, useState, type ReactNode } from "react";
import { useAppStore } from "../../store/useAppStore";
import type { AnimatedBuildControlDef } from "../../types";
import { normalizeAnimatedSlug, PLAYER_PROCEDURAL_BUILD_SLUG } from "../../utils/enemyDisplay";
import { animatedExportRelativePath, playerExportRelativePath } from "../../utils/glbVariants";
import { PLAYER_COLORS } from "../CommandPanel/commandLogic";
import { previewPathFromAssetsUrl } from "../../utils/previewPathFromAssetsUrl";
import {
  getMeshPartTree,
  type MeshPartTreeControlHints,
  type PartTreeNode,
} from "./quickSourceNav";
import { ControlRow, FloatControlsTable } from "./BuildControlRow";

const s = {
  bar: {
    background: "#1e1e1e",
    borderBottom: "1px solid #3c3c3c",
    padding: "4px 8px",
    display: "flex",
    gap: 8,
    alignItems: "center",
    flexWrap: "wrap",
    flexShrink: 0,
  },
  label: { color: "#9d9d9d", fontSize: 11 },
  select: {
    background: "#3c3c3c",
    color: "#d4d4d4",
    border: "1px solid #555",
    borderRadius: 3,
    padding: "2px 6px",
    fontSize: 11,
  },
  input: {
    background: "#3c3c3c",
    color: "#d4d4d4",
    border: "1px solid #555",
    borderRadius: 3,
    padding: "2px 6px",
    fontSize: 11,
    width: 56,
  },
  inputFloat: {
    background: "#3c3c3c",
    color: "#d4d4d4",
    border: "1px solid #555",
    borderRadius: 3,
    padding: "2px 6px",
    fontSize: 11,
    width: 64,
  },
  /** Rig float table — fixed height; scrolls when many rows. */
  rigFloatScrollWrap: {
    maxHeight: 280,
    overflowY: "auto" as const,
    overflowX: "auto" as const,
    flex: "0 1 auto",
    minWidth: 0,
    maxWidth: "100%",
    paddingTop: 2,
  },
  /** Mesh float table — fills panel height; scrolls when many rows. */
  meshFloatScrollWrap: {
    flex: 1,
    minHeight: 0,
    overflowY: "auto" as const,
    overflowX: "auto" as const,
    minWidth: 0,
    maxWidth: "100%",
    paddingTop: 2,
  },
  sectionHeaderRow: {
    display: "flex",
    alignItems: "center",
    gap: 10,
    flexWrap: "wrap",
  },
  sectionTitle: { color: "#9d9d9d", fontSize: 11, fontWeight: 600 } as const,
  filterInput: {
    background: "#2d2d2d",
    color: "#d4d4d4",
    border: "1px solid #555",
    borderRadius: 3,
    padding: "2px 6px",
    fontSize: 11,
    width: 128,
    flex: "0 0 auto",
  },
  warnText: { color: "#e2b714", fontSize: 11, maxWidth: 560 },
  treeRow: { display: "flex", gap: 6, alignItems: "center", flexWrap: "wrap" },
  tree: {
    background: "#252526",
    border: "1px solid #3c3c3c",
    borderRadius: 3,
    padding: "4px 6px",
    maxHeight: 280,
    overflowY: "auto" as const,
    fontSize: 11,
    color: "#c8c8c8",
    flexShrink: 0,
  },
  treeToggle: {
    background: "transparent",
    border: "none",
    color: "#9d9d9d",
    cursor: "pointer",
    fontSize: 11,
    padding: 0,
  },
} as const;

/** Spider multi-eye placement controls are inert when there is at most one eye. */
function spiderPlacementRowDisabled(defKey: string, values: Readonly<Record<string, unknown>>): boolean {
  const ec = values.eye_count;
  const eyeCount = typeof ec === "number" ? ec : 2;
  if (eyeCount <= 1) {
    return defKey === "eye_distribution" || defKey === "eye_uniform_shape" || defKey === "eye_clustering";
  }
  if (defKey === "eye_uniform_shape") {
    const ed = values.eye_distribution;
    return (typeof ed === "string" ? ed : "uniform") === "random";
  }
  return false;
}

function buildControlDisabled(
  slug: string,
  defKey: string,
  values: Readonly<Record<string, unknown>>,
): boolean {
  if (defKey === "pupil_shape" && !values["pupil_enabled"]) return true;
  if (defKey === "mouth_shape" && !values["mouth_enabled"]) return true;
  if ((defKey === "tail_shape" || defKey === "tail_length") && !values["tail_enabled"]) return true;
  return slug === "spider" && spiderPlacementRowDisabled(defKey, values);
}

function PartTreeRows({ nodes, depth }: { nodes: PartTreeNode[]; depth: number }) {
  return (
    <>
      {nodes.map((n) => (
        <div key={n.id}>
          <div style={{ paddingLeft: depth * 12, paddingTop: 2, paddingBottom: 2 }}>
            {n.children && n.children.length > 0 ? "▸ " : "• "}
            {n.label}
          </div>
          {n.children && n.children.length > 0 ? (
            <PartTreeRows nodes={n.children} depth={depth + 1} />
          ) : null}
        </div>
      ))}
    </>
  );
}

/**
 * Procedural build options for the selected animated enemy (preview always uses variant index 00).
 * Finish, base color, and pattern build options live on the Colors tab (`TextureControlsSection`).
 */
export function BuildControls() {
  const commandContext = useAppStore((st) => st.commandContext);
  const animatedEnemyMeta = useAppStore((st) => st.animatedEnemyMeta);
  const animatedBuildControls = useAppStore((st) => st.animatedBuildControls);
  const animatedBuildOptionValues = useAppStore((st) => st.animatedBuildOptionValues);
  const setAnimatedBuildOption = useAppStore((st) => st.setAnimatedBuildOption);
  const selectAssetByPath = useAppStore((st) => st.selectAssetByPath);
  const enemyMetaStatus = useAppStore((st) => st.enemyMetaStatus);
  const enemyMetaError = useAppStore((st) => st.enemyMetaError);
  const metaBackend = useAppStore((st) => st.metaBackend);
  const metaBackendDetail = useAppStore((st) => st.metaBackendDetail);
  const loadAnimatedEnemyMeta = useAppStore((st) => st.loadAnimatedEnemyMeta);
  const [meshFilter, setMeshFilter] = useState("");
  const [rigFilter, setRigFilter] = useState("");
  const [partsOpen, setPartsOpen] = useState(false);

  const { cmd, enemy } = commandContext;
  const playerColor = (enemy || "").trim().toLowerCase();
  const slug =
    cmd === "player" && PLAYER_COLORS.includes(playerColor)
      ? PLAYER_PROCEDURAL_BUILD_SLUG
      : normalizeAnimatedSlug(enemy);
  const buildOpts = animatedBuildOptionValues[slug] ?? {};

  const spiderEyeDef = animatedBuildControls["spider"]?.find(
    (d) => d.type === "select" && d.key === "eye_count",
  ) as { options?: number[]; default?: number } | undefined;
  const clawPeDef = animatedBuildControls["claw_crawler"]?.find(
    (d) => d.type === "int" && d.key === "peripheral_eyes",
  ) as { min?: number; max?: number } | undefined;
  const partTreeHints: MeshPartTreeControlHints = {
    spiderEyeOptions: spiderEyeDef?.options,
    spiderEyeDefault: spiderEyeDef?.default,
    clawPeripheralMin: clawPeDef?.min,
    clawPeripheralMax: clawPeDef?.max,
  };
  const partTree = getMeshPartTree(cmd, enemy, animatedEnemyMeta, buildOpts, partTreeHints);

  const isAnimatedEnemy =
    cmd === "animated" &&
    Boolean(slug) &&
    slug !== "all" &&
    animatedEnemyMeta.some((m) => m.slug === slug);

  const isPlayerSlimeBuild = cmd === "player" && PLAYER_COLORS.includes(playerColor);

  const defs = animatedBuildControls[slug] ?? [];
  /** Per-part materials (`feat_*`) on Colors; geometry extras (`extra_zone_*`) on Extras; surface texture on Colors. */
  const buildDefs = defs.filter(
    (d) =>
      !d.key.startsWith("feat_") &&
      !d.key.startsWith("extra_zone_") &&
      !d.key.startsWith("texture_"),
  );
  const controlSlugs = Object.keys(animatedBuildControls);

  useEffect(() => {
    if (enemyMetaStatus !== "idle") return;
    if (!isAnimatedEnemy && !isPlayerSlimeBuild) return;
    void loadAnimatedEnemyMeta();
  }, [
    enemyMetaStatus,
    loadAnimatedEnemyMeta,
    isAnimatedEnemy,
    isPlayerSlimeBuild,
  ]);

  useEffect(() => {
    if (!isAnimatedEnemy && !isPlayerSlimeBuild) return;
    const desired = isPlayerSlimeBuild
      ? playerExportRelativePath(playerColor, 0)
      : animatedExportRelativePath(slug, 0);
    const current = previewPathFromAssetsUrl(useAppStore.getState().activeGlbUrl);
    if (current === desired) return;
    selectAssetByPath(desired);
  }, [isAnimatedEnemy, isPlayerSlimeBuild, playerColor, slug, selectAssetByPath]);

  const meshPartTreeBlock = (
    <>
      <div style={s.treeRow}>
        <button type="button" style={s.treeToggle} onClick={() => setPartsOpen((o) => !o)}>
          {partsOpen ? "▼" : "▶"} Mesh parts (source)
        </button>
      </div>
      {partsOpen ? (
        <div style={s.tree}>
          <PartTreeRows nodes={partTree} depth={0} />
        </div>
      ) : null}
    </>
  );

  if (!isAnimatedEnemy && !isPlayerSlimeBuild) {
    return (
      <div
        style={{
          display: "flex",
          flexDirection: "column",
          alignItems: "stretch",
          gap: 8,
          padding: "8px 8px 12px",
          background: "#1e1e1e",
          color: "#9d9d9d",
          fontSize: 12,
          flex: 1,
          minHeight: 0,
        }}
      >
        {meshPartTreeBlock}
        <div style={{ padding: "4px 4px 0" }}>
          Set <strong style={{ color: "#bbb" }}>cmd</strong> to <code style={{ color: "#bbb" }}>animated</code> (enemy, not
          &quot;all&quot;) or <code style={{ color: "#bbb" }}>player</code> (color) to use build controls.
        </div>
      </div>
    );
  }

  if (defs.length === 0) {
    const busy = enemyMetaStatus === "loading";
    let detail: ReactNode = null;
    if (enemyMetaStatus === "ok") {
      if (metaBackend === "fallback") {
        detail = (
          <span style={s.warnText}>
            Server could not load Python build controls (ImportError). Run{" "}
            <code style={{ color: "#bbb" }}>task editor</code> from the repo root and ensure port 8000 is
            reachable. {metaBackendDetail ? ` — ${metaBackendDetail}` : ""}
          </span>
        );
      } else if (controlSlugs.length === 0) {
        detail = (
          <span style={{ color: "#9d9d9d", fontSize: 11 }}>
            API returned no control definitions. Open DevTools → Network → <code style={{ color: "#bbb" }}>/api/meta/enemies</code> and confirm{" "}
            <code style={{ color: "#bbb" }}>animated_build_controls</code> is non-empty.
          </span>
        );
      } else if (!controlSlugs.includes(slug)) {
        detail = (
          <span style={{ color: "#9d9d9d", fontSize: 11 }}>
            No controls for slug <code style={{ color: "#bbb" }}>{slug}</code>. Known: {controlSlugs.join(", ")}.
          </span>
        );
      } else {
        detail = (
          <span style={{ color: "#9d9d9d", fontSize: 11 }}>No build controls for this enemy (unexpected empty list).</span>
        );
      }
    } else if (enemyMetaStatus === "idle") {
      detail = (
        <span style={{ color: "#9d9d9d", fontSize: 11 }}>
          Waiting for enemy metadata…
        </span>
      );
    }

    return (
      <div
        style={{
          ...s.bar,
          flexDirection: "column",
          alignItems: "stretch",
          flex: 1,
          minHeight: 0,
          flexShrink: 1,
        }}
      >
        {meshPartTreeBlock}
        {busy ? (
          <span style={{ color: "#9d9d9d", fontSize: 11 }}>Loading build controls…</span>
        ) : enemyMetaStatus === "error" ? (
          <span style={{ color: "#f48771", fontSize: 11 }} title={enemyMetaError ?? ""}>
            {enemyMetaError ?? "Could not load build controls."} Start the asset editor API (port 8000) or check the Vite proxy.
          </span>
        ) : (
          detail
        )}
        <button
          type="button"
          style={{
            background: "#3c3c3c",
            color: "#d4d4d4",
            border: "1px solid #555",
            borderRadius: 3,
            padding: "2px 8px",
            fontSize: 11,
            cursor: busy ? "wait" : "pointer",
          }}
          disabled={busy}
          onClick={() => loadAnimatedEnemyMeta()}
        >
          Retry
        </button>
      </div>
    );
  }

  const values = animatedBuildOptionValues[slug] ?? {};
  const nonFloat = buildDefs.filter((d) => d.type !== "float");
  const allFloats = buildDefs.filter((d) => d.type === "float");
  const rigFloats = allFloats.filter((d) => d.key.startsWith("RIG_"));
  const meshFloats = allFloats.filter((d) => !d.key.startsWith("RIG_"));

  const rq = rigFilter.trim().toLowerCase();
  const rigFiltered = rq
    ? rigFloats.filter(
        (d) => d.key.toLowerCase().includes(rq) || d.label.toLowerCase().includes(rq),
      )
    : rigFloats;

  const q = meshFilter.trim().toLowerCase();
  const meshFiltered = q
    ? meshFloats.filter(
        (d) => d.key.toLowerCase().includes(q) || d.label.toLowerCase().includes(q),
      )
    : meshFloats;

  function floatSection(
    label: string,
    sectionFloats: typeof allFloats,
    filtered: typeof allFloats,
    filterValue: string,
    setFilter: (v: string) => void,
    filterPlaceholder: string,
    filterAria: string,
    scrollWrapStyle: typeof s.rigFloatScrollWrap | typeof s.meshFloatScrollWrap,
    flexGrow: boolean,
  ) {
    if (sectionFloats.length === 0) return null;
    const body = (
      <>
        <div style={s.sectionHeaderRow}>
          <span style={s.sectionTitle}>{label}</span>
          <input
            type="search"
            placeholder={filterPlaceholder}
            aria-label={filterAria}
            value={filterValue}
            onChange={(e) => setFilter(e.target.value)}
            style={s.filterInput}
          />
        </div>
        <FloatControlsTable
          defs={filtered}
          values={values}
          scrollWrapStyle={scrollWrapStyle}
          onFloatChange={(key, v) => setAnimatedBuildOption(slug, key, v)}
          isRowDisabled={(key) => buildControlDisabled(slug, key, values)}
        />
      </>
    );
    return (
      <div
        style={
          flexGrow
            ? {
                flex: 1,
                minHeight: 0,
                display: "flex",
                flexDirection: "column",
                gap: 10,
              }
            : {
                display: "flex",
                flexDirection: "column",
                gap: 10,
                marginTop: 6,
              }
        }
      >
        {body}
      </div>
    );
  }

  return (
    <div
      style={{
        ...s.bar,
        flexDirection: "column",
        alignItems: "stretch",
        gap: 10,
        flex: 1,
        minHeight: 0,
        flexShrink: 1,
      }}
    >
      {meshPartTreeBlock}
      {buildDefs.length === 0 && defs.length > 0 ? (
        <span style={{ color: "#9d9d9d", fontSize: 11 }}>
          No mesh or rig numeric fields here for this enemy — per-part finishes and hex colors are on the{" "}
          <strong style={{ color: "#bbb" }}>Colors</strong> tab.
        </span>
      ) : null}
      {nonFloat.map((def) => {
        const dis = buildControlDisabled(slug, def.key, values);
        return (
          <div key={def.key}>
            <div style={{ opacity: dis ? 0.42 : 1, pointerEvents: dis ? "none" : undefined }}>
              <ControlRow
                def={def}
                value={values[def.key]}
                onChange={(v: number | string | boolean) => setAnimatedBuildOption(slug, def.key, v)}
              />
            </div>
          </div>
        );
      })}
      {floatSection(
        "Rig",
        rigFloats,
        rigFiltered,
        rigFilter,
        setRigFilter,
        "Filter rig…",
        "Filter rig (bone layout) parameters",
        s.rigFloatScrollWrap,
        false,
      )}
      {floatSection(
        "Mesh",
        meshFloats,
        meshFiltered,
        meshFilter,
        setMeshFilter,
        "Filter mesh…",
        "Filter mesh parameters",
        s.meshFloatScrollWrap,
        true,
      )}
    </div>
  );
}
