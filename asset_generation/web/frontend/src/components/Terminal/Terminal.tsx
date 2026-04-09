import { useEffect, useRef } from "react";
import Convert from "ansi-to-html";
import { useAppStore } from "../../store/useAppStore";

const converter = new Convert({ escapeXML: true });

const styles: Record<string, React.CSSProperties> = {
  container: {
    background: "#0d0d0d",
    color: "#d4d4d4",
    fontFamily: "'Cascadia Code', 'Fira Code', 'Consolas', monospace",
    fontSize: "12px",
    lineHeight: "1.5",
    padding: "8px",
    overflowY: "auto",
    height: 180,
    maxHeight: "28vh",
    minHeight: 120,
    flexShrink: 0,
  },
  line: {
    whiteSpace: "pre-wrap",
    wordBreak: "break-all",
  },
};

export function Terminal() {
  const lines = useAppStore((s) => s.terminalLines);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const el = bottomRef.current;
    if (el && typeof el.scrollIntoView === "function") {
      el.scrollIntoView({ behavior: "smooth" });
    }
  }, [lines]);

  return (
    <div style={styles.container}>
      {lines.map((l) => (
        <div
          key={l.id}
          style={styles.line}
          dangerouslySetInnerHTML={{ __html: converter.toHtml(l.text) }}
        />
      ))}
      <div ref={bottomRef} />
    </div>
  );
}
