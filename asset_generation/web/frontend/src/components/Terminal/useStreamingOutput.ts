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
}

export function useStreamingOutput() {
  const esRef = useRef<EventSource | null>(null);
  const appendLine = useAppStore((s) => s.appendLine);
  const setIsRunning = useAppStore((s) => s.setIsRunning);
  const refreshAssetsAndAutoSelect = useAppStore((s) => s.refreshAssetsAndAutoSelect);

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

    const url = `${endpoint}?${params.toString()}`;
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
