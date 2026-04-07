import { useEffect, useState, type ReactNode } from "react";
import { useAppStore } from "../../store/useAppStore";
import type { AnimatedBuildControlDef } from "../../types";
import { normalizeAnimatedSlug } from "../../utils/enemyDisplay";
import { animatedExportRelativePath } from "../../utils/glbVariants";
import {
  getMeshPartTree,
  type MeshPartTreeControlHints,
  type PartTreeNode,
} from "./quickSourceNav";

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
  /** Rig float controls — fixed cap so Mesh can take remaining column height. */
  rigScroll: {
    display: "flex",
    gap: 8,
    alignItems: "center",
    flexWrap: "wrap",
    maxHeight: 220,
    overflowY: "auto" as const,
    flex: "0 1 auto",
    minWidth: 0,
    maxWidth: "100%",
  },
  /** Mesh float controls — grows with the build panel; scrolls inside. */
  meshScrollGrow: {
    display: "flex",
    gap: 8,
    alignItems: "center",
    flexWrap: "wrap",
    alignContent: "flex-start",
    flex: 1,
    minHeight: 0,
    overflowY: "auto" as const,
    minWidth: 0,
    maxWidth: "100%",
  },
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

function ControlRow({
  def,
  value,
  onChange,
}: {
  def: AnimatedBuildControlDef;
  value: unknown;
  onChange: (v: number) => void;
}) {
  if (def.type === "float") {
    return <FloatRow def={def} value={value} onChange={onChange} />;
  }
  if (def.type === "select") {
    const n = typeof value === "number" ? value : def.default;
    return (
      <label style={{ display: "flex", gap: 4, alignItems: "center" }}>
        <span style={s.label}>{def.label}</span>
        <select
          style={s.select}
          value={n}
          onChange={(e) => onChange(Number(e.target.value))}
        >
          {def.options.map((opt) => (
            <option key={opt} value={opt}>
              {opt}
            </option>
          ))}
        </select>
      </label>
    );
  }
  const n = typeof value === "number" ? value : def.default;
  return (
    <label style={{ display: "flex", gap: 4, alignItems: "center" }}>
      <span style={s.label}>{def.label}</span>
      <input
        style={s.input}
        type="number"
        min={def.min}
        max={def.max}
        value={n}
        onChange={(e) => onChange(Number(e.target.value))}
      />
    </label>
  );
}

function FloatRow({
  def,
  value,
  onChange,
}: {
  def: Extract<AnimatedBuildControlDef, { type: "float" }>;
  value: unknown;
  onChange: (v: number) => void;
}) {
  const n = typeof value === "number" ? value : def.default;
  return (
    <label
      style={{
        display: "flex",
        gap: 6,
        alignItems: "center",
        flexWrap: "wrap",
        maxWidth: "100%",
      }}
    >
      <span style={s.label} title={def.key}>
        {def.label}
      </span>
      <input
        type="range"
        min={def.min}
        max={def.max}
        step={def.step}
        value={n}
        onChange={(e) => onChange(Number(e.target.value))}
        aria-label={def.label}
        style={{ flex: "1 1 72px", minWidth: 72, maxWidth: 160 }}
      />
      <input
        style={s.inputFloat}
        type="number"
        step={def.step}
        min={def.min}
        max={def.max}
        value={n}
        onChange={(e) => onChange(Number(e.target.value))}
      />
    </label>
  );
}

/**
 * Procedural build options for the selected animated enemy (preview always uses variant index 00).
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
  const slug = normalizeAnimatedSlug(enemy);
  const buildOpts = animatedBuildOptionValues[normalizeAnimatedSlug(enemy)] ?? {};
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

  useEffect(() => {
    if (!isAnimatedEnemy) return;
    selectAssetByPath(animatedExportRelativePath(slug, 0));
  }, [isAnimatedEnemy, slug, selectAssetByPath]);

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

  if (!isAnimatedEnemy) {
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
          Set <strong style={{ color: "#bbb" }}>cmd</strong> to <code style={{ color: "#bbb" }}>animated</code> and pick an
          enemy (not &quot;all&quot;) to use build controls.
        </div>
      </div>
    );
  }

  const defs = animatedBuildControls[slug] ?? [];
  const controlSlugs = Object.keys(animatedBuildControls);

  if (defs.length === 0) {
    const busy = enemyMetaStatus === "loading" || enemyMetaStatus === "idle";
    let detail: ReactNode = null;
    if (!busy && enemyMetaStatus === "ok") {
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
    }

    return (
      <div style={{ ...s.bar, flexDirection: "column", alignItems: "stretch", flex: 1, minHeight: 0 }}>
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
  const nonFloat = defs.filter((d) => d.type !== "float");
  const allFloats = defs.filter((d) => d.type === "float");
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
    scrollStyle: typeof s.rigScroll | typeof s.meshScrollGrow,
    flexGrow: boolean,
  ) {
    if (sectionFloats.length === 0) return null;
    const body = (
      <>
        <span style={s.label}>{label}</span>
        <input
          type="search"
          placeholder={filterPlaceholder}
          aria-label={filterAria}
          value={filterValue}
          onChange={(e) => setFilter(e.target.value)}
          style={s.filterInput}
        />
        <div style={scrollStyle}>
          {filtered.map((def) => (
            <ControlRow
              key={def.key}
              def={def}
              value={values[def.key]}
              onChange={(v) => setAnimatedBuildOption(slug, def.key, v)}
            />
          ))}
        </div>
      </>
    );
    if (flexGrow) {
      return (
        <div
          style={{
            flex: 1,
            minHeight: 0,
            display: "flex",
            flexDirection: "column",
            gap: 8,
          }}
        >
          {body}
        </div>
      );
    }
    return body;
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
      {nonFloat.map((def) => (
        <ControlRow
          key={def.key}
          def={def}
          value={values[def.key]}
          onChange={(v) => setAnimatedBuildOption(slug, def.key, v)}
        />
      ))}
      {floatSection(
        "Rig",
        rigFloats,
        rigFiltered,
        rigFilter,
        setRigFilter,
        "Filter rig…",
        "Filter rig (bone layout) parameters",
        s.rigScroll,
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
        s.meshScrollGrow,
        true,
      )}
    </div>
  );
}
