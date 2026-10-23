import { useState } from "react";
import { AddCampaignModal, CampaignCard, useCampaigns, type Campaign } from "../../domains/campaign";
import { ThemeToggle } from "../../ui/components";
import styles from "./CampaignPicker.module.css";

type CampaignPickerProps = {
  email: string | undefined;
  onOpen: (campaign: Campaign) => void;
  /** The GM's own library, outside any campaign (ADR-0027). */
  onOpenLibrary: () => void;
  onSignOut: () => void;
};

/** The landing screen after sign-in (docs/design/overview.md §2). */
export function CampaignPicker({ email, onOpen, onOpenLibrary, onSignOut }: CampaignPickerProps) {
  const campaigns = useCampaigns();
  const [adding, setAdding] = useState(false);
  const empty = campaigns.data?.length === 0;

  return (
    <div className={styles.page}>
      <header className={styles.header}>
        <div className={styles.brand}>
          <span className={styles.tile} aria-hidden>
            <img src="/quillbert-mark.svg" alt="" />
          </span>
          <span className={styles.brandName}>Quillbert</span>
        </div>
        <div className={styles.account}>
          <button type="button" className={styles.signOut} onClick={onOpenLibrary}>
            My library
          </button>
          <ThemeToggle />
          <button type="button" className={styles.signOut} onClick={onSignOut}>
            Sign out
          </button>
          {/* Opens Settings once that screen exists. */}
          <span className={styles.avatar} title={email}>
            {(email ?? "?").slice(0, 1).toUpperCase()}
          </span>
        </div>
      </header>

      <main className={styles.main}>
        <h1 className={styles.title}>Your Campaigns</h1>
        <p className={styles.sub}>
          {empty ? "No campaigns yet. Start your first table." : "Pick up where you left off, or start a new table."}
        </p>

        {campaigns.isError ? (
          <p className={styles.error} role="alert">
            Could not load your campaigns. {campaigns.error.message}{" "}
            <button type="button" className={styles.retry} onClick={() => void campaigns.refetch()}>
              Try again
            </button>
          </p>
        ) : (
          <div className={styles.grid} aria-busy={campaigns.isPending}>
            {campaigns.data?.map((campaign) => (
              <CampaignCard key={campaign.id} campaign={campaign} onOpen={() => onOpen(campaign)} />
            ))}
            {!campaigns.isPending && (
              <button type="button" className={styles.add} onClick={() => setAdding(true)}>
                <span className={styles.plus} aria-hidden>
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6">
                    <path d="M12 5v14M5 12h14" strokeLinecap="round" />
                  </svg>
                </span>
                <span className={styles.addTitle}>New campaign</span>
                <span className={styles.addSub}>Start a fresh table</span>
              </button>
            )}
          </div>
        )}
      </main>

      {adding && <AddCampaignModal onClose={() => setAdding(false)} onCreated={onOpen} />}
    </div>
  );
}
