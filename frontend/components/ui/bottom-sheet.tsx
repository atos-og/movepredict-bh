import type { ReactNode } from "react";

type BottomSheetProps = {
  children: ReactNode;
  className?: string;
  open?: boolean;
};

export function BottomSheet({ children, className = "", open = true }: BottomSheetProps) {
  return (
    <aside className={`bottom-sheet ${open ? "bottom-sheet-open" : ""} ${className}`.trim()}>
      <div className="bottom-sheet-handle" aria-hidden="true" />
      {children}
    </aside>
  );
}
