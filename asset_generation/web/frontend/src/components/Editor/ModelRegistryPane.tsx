import { useCallback, useEffect, useState, type CSSProperties } from "react";
import { fetchModelRegistry, patchRegistryEnemyVersion } from "../../api/client";
import type { ModelRegistryPayload, RegistryEnemyVersion } from "../../types";

const noteStyle = { fontSize: 11, color: "#9d9d9d", marginBottom: 12, lineHeight: 1.45 };

export function ModelRegistryPane() {
  const [data, setData] = useState<ModelRegistryPayload | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busyKey, setBusyKey] = useState<string | null>(null);

  const reload = useCallback(() => {
    setError(null);
    fetchModelRegistry()
      .then(setData)
      .catch((e: unknown) => {
        setError(e instanceof Error ? e.message : String(e));
      });
  }, []);

  useEffect(() => {
    reload();
  }, [reload]);

  async function applyFlags(family: string, v: RegistryEnemyVersion, nextDraft: boolean, nextInUse: boolean) {
    const key = `${family}:${v.id}`;
    setBusyKey(key);
    setError(null);
    try {
      const use = nextDraft ? false : nextInUse;
      const updated = await patchRegistryEnemyVersion(family, v.id, {
        draft: nextDraft,
        in_use: use,
      });
      setData(updated);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : String(e));
    } finally {
      setBusyKey(null);
    }
  }

  if (!data && !error) {
    return (
      <div style={{ padding: 16, color: "#9d9d9d", fontSize: 12 }}>
        Loading model registry…
      </div>
    );
  }

  if (error && !data) {
    return (
      <div style={{ padding: 16 }}>
        <div style={{ color: "#f14c4c", fontSize: 12, marginBottom: 8 }}>{error}</div>
        <button type="button" onClick={reload} style={btnSecondary}>
          Retry
        </button>
      </div>
    );
  }

  if (!data) return null;

  const families = Object.keys(data.enemies).sort();

  return (
    <div style={{ padding: 12, color: "#d4d4d4", fontSize: 12, overflow: "auto", flex: 1 }}>
      <div style={noteStyle}>
        <strong>Draft</strong> exports are excluded from the default spawn pool until promoted (MRVC-4).
        <strong> Demotion:</strong> mark <strong>Draft</strong> — the version leaves the in-use pool but stays on disk.
      </div>
      {error && (
        <div style={{ color: "#f14c4c", marginBottom: 8, fontSize: 11 }}>{error}</div>
      )}
      <table style={{ width: "100%", borderCollapse: "collapse", fontSize: 11 }}>
        <thead>
          <tr style={{ textAlign: "left", borderBottom: "1px solid #3c3c3c" }}>
            <th style={th}>Family</th>
            <th style={th}>Version id</th>
            <th style={th}>Path</th>
            <th style={th}>Draft</th>
            <th style={th}>In pool</th>
          </tr>
        </thead>
        <tbody>
          {families.map((fam) =>
            data.enemies[fam].versions.map((row) => {
              const key = `${fam}:${row.id}`;
              const pending = busyKey === key;
              return (
                <tr key={key} style={{ borderBottom: "1px solid #2d2d2d" }}>
                  <td style={td}>{fam}</td>
                  <td style={td}>{row.id}</td>
                  <td style={{ ...td, wordBreak: "break-all" }}>{row.path}</td>
                  <td style={td}>
                    <input
                      type="checkbox"
                      checked={row.draft}
                      disabled={pending}
                      onChange={(e) => {
                        const d = e.target.checked;
                        applyFlags(fam, row, d, d ? false : row.in_use);
                      }}
                    />
                  </td>
                  <td style={td}>
                    <input
                      type="checkbox"
                      checked={row.in_use && !row.draft}
                      disabled={pending || row.draft}
                      onChange={(e) => {
                        applyFlags(fam, row, row.draft, e.target.checked);
                      }}
                    />
                  </td>
                </tr>
              );
            }),
          )}
        </tbody>
      </table>
      <div style={{ marginTop: 16, ...noteStyle }}>
        Persisted to <code style={{ color: "#ce9178" }}>asset_generation/python/model_registry.json</code> via API
        (atomic write; only this manifest path is modified).
      </div>
    </div>
  );
}

const th: CSSProperties = { padding: "6px 8px", color: "#9d9d9d", fontWeight: 600 };
const td: CSSProperties = { padding: "6px 8px", verticalAlign: "middle" };
const btnSecondary: CSSProperties = {
  padding: "4px 10px",
  fontSize: 11,
  border: "1px solid #555",
  borderRadius: 3,
  cursor: "pointer",
  background: "#3c3c3c",
  color: "#d4d4d4",
};
