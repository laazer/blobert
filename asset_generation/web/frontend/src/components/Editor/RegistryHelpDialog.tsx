import { useEffect, useId, type CSSProperties, type ReactNode } from "react";
import { createPortal } from "react-dom";

const overlay: CSSProperties = {
  position: "fixed",
  inset: 0,
  background: "rgba(0,0,0,0.55)",
  zIndex: 10000,
  display: "flex",
  alignItems: "center",
  justifyContent: "center",
  padding: 16,
};
const dialog: CSSProperties = {
  background: "#252526",
  border: "1px solid #3c3c3c",
  borderRadius: 6,
  padding: 16,
  maxWidth: 520,
  width: "100%",
  maxHeight: "90vh",
  overflowY: "auto",
  display: "flex",
  flexDirection: "column",
  gap: 10,
  boxShadow: "0 8px 32px rgba(0,0,0,0.45)",
};
const titleStyle: CSSProperties = { margin: 0, fontSize: 14, color: "#e0e0e0", fontWeight: 600 };
const bodyStyle: CSSProperties = { margin: 0, fontSize: 11, color: "#9d9d9d", lineHeight: 1.5 };
const btn: CSSProperties = {
  padding: "6px 14px",
  fontSize: 12,
  borderRadius: 3,
  cursor: "pointer",
  border: "1px solid #555",
  background: "#3c3c3c",
  color: "#d4d4d4",
  alignSelf: "flex-end",
};
const infoBtn: CSSProperties = {
  padding: "2px 8px",
  fontSize: 11,
  border: "1px solid #555",
  borderRadius: 3,
  cursor: "pointer",
  background: "#2d2d2d",
  color: "#9d9d9d",
  lineHeight: 1.4,
};

export type RegistryHelpDialogProps = {
  open: boolean;
  title: string;
  onClose: () => void;
  children: ReactNode;
};

export function RegistryHelpDialog({ open, title, onClose, children }: RegistryHelpDialogProps) {
  const titleId = useId();

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  if (!open) return null;

  return createPortal(
    <div
      style={overlay}
      role="presentation"
      onMouseDown={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div role="dialog" aria-modal="true" aria-labelledby={titleId} style={dialog}>
        <h4 id={titleId} style={titleStyle}>
          {title}
        </h4>
        <div style={bodyStyle}>{children}</div>
        <button type="button" style={btn} onClick={onClose}>
          Close
        </button>
      </div>
    </div>,
    document.body,
  );
}

export type RegistryInfoButtonProps = {
  "aria-label": string;
  title: string;
  dialogTitle: string;
  open: boolean;
  onOpen: () => void;
  onClose: () => void;
  children: ReactNode;
};

export function RegistryInfoButton({
  "aria-label": ariaLabel,
  title: buttonTitle,
  dialogTitle,
  open,
  onOpen,
  onClose,
  children,
}: RegistryInfoButtonProps) {
  return (
    <>
      <button
        type="button"
        style={infoBtn}
        aria-label={ariaLabel}
        title={buttonTitle}
        data-testid="registry-enemy-versions-info"
        onClick={onOpen}
      >
        Info
      </button>
      <RegistryHelpDialog open={open} title={dialogTitle} onClose={onClose}>
        {children}
      </RegistryHelpDialog>
    </>
  );
}
