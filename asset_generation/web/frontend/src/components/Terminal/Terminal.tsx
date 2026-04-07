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
    flexGrow: 1,
    minHeight: 200,
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
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
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
