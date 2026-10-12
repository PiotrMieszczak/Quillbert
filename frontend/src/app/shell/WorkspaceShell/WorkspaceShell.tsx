import { useEffect, type ReactNode } from "react";
import { AssistantPanel } from "../../../domains/assistant";
import type { Campaign } from "../../../domains/campaign";
import { Header } from "../Header";
import { NavRail } from "../NavRail";
import { TabBar } from "../TabBar";
import { useLayoutMode, useShellStore } from "../store";
import styles from "./WorkspaceShell.module.css";

type WorkspaceShellProps = {
  campaign: Campaign;
  activeView: string;
  onNavigate: (id: string) => void;
  children: ReactNode;
};

export function WorkspaceShell({
  campaign,
  activeView,
  onNavigate,
  children,
}: WorkspaceShellProps) {
  useLayoutMode();
  const mob = useShellStore((state) => state.mob);
  const panelOpen = useShellStore((state) => state.panelOpen);
  const openPanel = useShellStore((state) => state.openPanel);
  const closePanel = useShellStore((state) => state.closePanel);

  useEffect(() => {
    if (!panelOpen) return;
    const onKey = (event: KeyboardEvent) => {
      if (event.key === "Escape") closePanel();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [panelOpen, closePanel]);

  return (
    <div className={[styles.shell, panelOpen && styles.panelOpen].filter(Boolean).join(" ")}>
      <Header campaign={campaign} />
      <NavRail active={activeView} onNavigate={onNavigate} />
      <main className={styles.main}>{children}</main>
      {mob && panelOpen && (
        <button
          type="button"
          className={styles.backdrop}
          aria-label="Close assistant"
          onClick={closePanel}
        />
      )}
      <aside className={styles.panelSlot} aria-hidden={!panelOpen} inert={!panelOpen || undefined}>
        <AssistantPanel onClose={closePanel} />
      </aside>
      <TabBar active={activeView} onNavigate={onNavigate} />
      {!panelOpen && (
        <button type="button" className={styles.fab} onClick={openPanel}>
          <span aria-hidden>✦</span>
          <span className={styles.fabLabel}>Assistant</span>
        </button>
      )}
    </div>
  );
}
