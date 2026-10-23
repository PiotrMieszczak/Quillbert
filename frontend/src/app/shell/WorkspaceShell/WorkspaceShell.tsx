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
  onSwitchCampaign: () => void;
  onSignOut: () => void;
  onOpenSource: (documentId: string) => void;
  children: ReactNode;
};

export function WorkspaceShell({
  campaign,
  activeView,
  onNavigate,
  onSwitchCampaign,
  onSignOut,
  onOpenSource,
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
      <Header campaign={campaign} onSwitchCampaign={onSwitchCampaign} onSignOut={onSignOut} />
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
      <aside className={styles.panelSlot}>
        {!mob && !panelOpen && (
          <div className={styles.rail}>
            <button type="button" className={styles.railSpark} onClick={openPanel} title="Open Quillbert (⌘K)" aria-label="Open Quillbert">
              ✦
            </button>
            <kbd className={styles.railKbd} aria-hidden>
              ⌘K
            </kbd>
            <button type="button" className={styles.railLabel} onClick={openPanel} tabIndex={-1}>
              <span>Ask Quillbert</span>
            </button>
          </div>
        )}
        <div className={styles.panelBody} aria-hidden={!panelOpen} inert={!panelOpen || undefined}>
          <AssistantPanel
            key={campaign.id}
            campaign={campaign}
            open={panelOpen}
            onOpen={openPanel}
            onClose={closePanel}
            // On a phone the sheet covers the library, so step aside to show the source.
            onOpenSource={(documentId) => {
              if (mob) closePanel();
              onOpenSource(documentId);
            }}
          />
        </div>
      </aside>
      <TabBar active={activeView} onNavigate={onNavigate} />
      {mob && !panelOpen && (
        <button type="button" className={styles.fab} onClick={openPanel} aria-label="Open Quillbert">
          ✦
        </button>
      )}
    </div>
  );
}
