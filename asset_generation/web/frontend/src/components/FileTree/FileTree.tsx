import { useEffect } from "react";
import { useAppStore } from "../../store/useAppStore";
import { FileNode } from "../../types";

const s: Record<string, React.CSSProperties> = {
  container: {
    background: "#252526",
    overflowY: "auto",
    height: "100%",
    padding: "4px 0",
    borderRight: "1px solid #3c3c3c",
    userSelect: "none",
  },
  header: {
    padding: "6px 12px",
    color: "#bbb",
    fontSize: 11,
    fontWeight: 600,
    letterSpacing: "0.08em",
    textTransform: "uppercase",
    borderBottom: "1px solid #3c3c3c",
    marginBottom: 4,
  },
};

function FileItem({ node, depth, selectedFile, onSelect }: {
  node: FileNode;
  depth: number;
  selectedFile: string | null;
  onSelect: (path: string) => void;
}) {
  const indent = depth * 12 + 8;
  const isSelected = node.type === "file" && node.path === selectedFile;

  if (node.type === "dir") {
    return (
      <div>
        <div style={{ paddingLeft: indent, color: "#e2b714", fontSize: 12, padding: `2px 0 2px ${indent}px` }}>
          {node.name}/
        </div>
        {node.children?.map((child) => (
          <FileItem key={child.path} node={child} depth={depth + 1} selectedFile={selectedFile} onSelect={onSelect} />
        ))}
      </div>
    );
  }

  return (
    <div
      onClick={() => onSelect(node.path)}
      style={{
        paddingLeft: indent,
        padding: `2px 0 2px ${indent}px`,
        cursor: "pointer",
        background: isSelected ? "#094771" : "transparent",
        color: isSelected ? "#fff" : "#d4d4d4",
        fontSize: 12,
        whiteSpace: "nowrap",
        overflow: "hidden",
        textOverflow: "ellipsis",
      }}
    >
      {node.name}
    </div>
  );
}

export function FileTree() {
  const fileTree = useAppStore((s) => s.fileTree);
  const selectedFile = useAppStore((s) => s.selectedFile);
  const loadFileTree = useAppStore((s) => s.loadFileTree);
  const selectFile = useAppStore((s) => s.selectFile);

  useEffect(() => {
    loadFileTree();
  }, []);

  return (
    <div style={s.container}>
      <div style={s.header}>src/</div>
      {fileTree.map((node) => (
        <FileItem key={node.path} node={node} depth={0} selectedFile={selectedFile} onSelect={selectFile} />
      ))}
    </div>
  );
}
