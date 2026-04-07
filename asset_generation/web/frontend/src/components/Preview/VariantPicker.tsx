import { useEffect, useMemo } from "react";
import { useAppStore } from "../../store/useAppStore";
import {
  assetByPath,
  parseAssetPathFromGlbUrl,
  parseVariantFilename,
  variantsInSameFamily,
} from "../../utils/glbVariants";

const s = {
  bar: {
    background: "#1e1e1e",
    borderBottom: "1px solid #3c3c3c",
    padding: "4px 8px",
    display: "flex",
    gap: 6,
    alignItems: "center",
    flexWrap: "wrap",
    flexShrink: 0,
  },
  label: { color: "#9d9d9d", fontSize: 11 },
  btn: {
    background: "#3c3c3c",
    color: "#d4d4d4",
    border: "1px solid #555",
    borderRadius: 3,
    padding: "2px 8px",
    cursor: "pointer",
    fontSize: 11,
  },
  btnActive: {
    background: "#0e639c",
    border: "1px solid #0e639c",
    color: "#fff",
  },
} as const;

export function VariantPicker() {
  const assets = useAppStore((st) => st.assets);
  const activeGlbUrl = useAppStore((st) => st.activeGlbUrl);
  const loadAssets = useAppStore((st) => st.loadAssets);
  const selectAssetByPath = useAppStore((st) => st.selectAssetByPath);

  useEffect(() => {
    loadAssets().catch(() => {});
  }, [loadAssets]);

  const activePath = parseAssetPathFromGlbUrl(activeGlbUrl);
  const activeAsset = useMemo(() => assetByPath(assets, activePath), [assets, activePath]);

  const variants = useMemo(
    () => variantsInSameFamily(assets, activeAsset),
    [assets, activeAsset],
  );

  if (!activeAsset || variants.length <= 1) {
    return null;
  }

  return (
    <div style={s.bar}>
      <span style={s.label}>Variant</span>
      {variants.map((a) => {
        const p = parseVariantFilename(a.name);
        const label = p ? String(p.variantIndex).padStart(2, "0") : a.name;
        const isActive = a.path === activePath;
        return (
          <button
            key={a.path}
            type="button"
            style={{ ...s.btn, ...(isActive ? s.btnActive : {}) }}
            title={a.name}
            onClick={() => selectAssetByPath(a.path)}
          >
            {label}
          </button>
        );
      })}
    </div>
  );
}
