import { useRef } from "react";
import { useAppStore } from "../../store/useAppStore";
import { RunCmd } from "../../types";

interface RunOptions {
  cmd: RunCmd;
  enemy?: string;
  count?: number;
  description?: string;
  difficulty?: string;
  finish?: string;
  hexColor?: string;
  /** JSON string for `BLOBERT_BUILD_OPTIONS_JSON` (animated + procedural player slime). */
  buildOptionsJson?: string;
  /** When true, GLBs write under `animated_exports/draft`, `player_exports/draft`, or `level_exports/draft`. */
  outputDraft?: boolean;
  /** When set, `BLOBERT_EXPORT_START_INDEX` pins to this variant (overwrite) instead of next free index. */
  replaceVariantIndex?: number;
}

export function useStreamingOutput() {
  const esRef = useRef<EventSource | null>(null);
  const appendLine = useAppStore((s) => s.appendLine);
  const setIsRunning = useAppStore((s) => s.setIsRunning);
  const refreshAssetsAndAutoSelect = useAppStore((s) => s.refreshAssetsAndAutoSelect);
  const bumpRegistryReload = useAppStore((s) => s.bumpRegistryReload);

  function start(options: RunOptions, endpoint = "/api/run/stream") {
    if (esRef.current) {
      esRef.current.close();
    }

    const params = new URLSearchParams();
    params.set("cmd", options.cmd);
    if (options.enemy) params.set("enemy", options.enemy);
    if (options.count != null && Number.isFinite(options.count) && options.count > 0) {
      params.set("count", String(options.count));
    }
    if (options.description) params.set("description", options.description);
    if (options.difficulty) params.set("difficulty", options.difficulty);
    if (options.finish) params.set("finish", options.finish);
    if (options.hexColor) params.set("hex_color", options.hexColor);
    if (options.buildOptionsJson) params.set("build_options", options.buildOptionsJson);
    if (options.outputDraft) params.set("output_draft", "true");
    if (
      options.replaceVariantIndex != null &&
      Number.isFinite(options.replaceVariantIndex)
    ) {
      params.set("replace_variant_index", String(Math.floor(options.replaceVariantIndex)));
    }

    const url = `${endpoint}?${params.toString()}`;
    console.log("[useStreamingOutput] Request URL:", url);
    if (options.buildOptionsJson) {
      console.log("[useStreamingOutput] build_options param:", options.buildOptionsJson);
    }
    const es = new EventSource(url);
    esRef.current = es;
    setIsRunning(true);

    es.addEventListener("log", (e: MessageEvent) => {
      try {
        const { line } = JSON.parse(e.data);
        appendLine(line);
      } catch {
        appendLine(e.data);
      }
    });

    es.addEventListener("done", (e: MessageEvent) => {
      try {
        const { output_file } = JSON.parse(e.data);
        appendLine("--- Done (exit 0) ---");
        refreshAssetsAndAutoSelect(output_file ?? null);
        bumpRegistryReload();
      } catch {
        appendLine("--- Done ---");
      }
      setIsRunning(false);
      es.close();
      esRef.current = null;
    });

    es.addEventListener("error", (e: MessageEvent) => {
      try {
        const { message, exit_code } = JSON.parse(e.data);
        appendLine(`--- Error (exit ${exit_code}): ${message} ---`);
      } catch {
        appendLine("--- Stream error ---");
      }
      setIsRunning(false);
      es.close();
      esRef.current = null;
    });

    // Network-level error
    es.onerror = () => {
      appendLine("--- Connection lost ---");
      setIsRunning(false);
      es.close();
      esRef.current = null;
    };
  }

  return { start };
}
