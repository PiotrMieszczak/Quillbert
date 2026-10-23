import { useState } from "react";
import { type Campaign, useSystems } from "../../domains/campaign";
import { DocumentLibrary } from "../../domains/library";
import { PageTitle } from "../../ui/components";
import styles from "./Documents.module.css";

/** A document to scroll to and highlight, e.g. from a citation chip. */
export type DocumentFocus = { documentId: string; at: number };

export function Documents({ campaign, focus }: { campaign: Campaign; focus: DocumentFocus | null }) {
  // The GM's library is read by every campaign of theirs (ADR-0027); add to it from here too.
  const [chosen, setChosen] = useState<{ shelf: "campaign" | "library"; at: number }>({ shelf: "campaign", at: 0 });
  // A citation chip opens a campaign document, so a citation newer than the tab choice wins.
  const shelf = focus && focus.at > chosen.at ? "campaign" : chosen.shelf;
  const setShelf = (next: "campaign" | "library") => setChosen({ shelf: next, at: focus?.at ?? 0 });
  // Files added from a campaign start on its system; the campaign carries the name, not the id.
  const systemId = useSystems().data?.find((system) => system.name === campaign.system)?.id;

  return (
    <div className={styles.view}>
      <header className={styles.header}>
        <PageTitle>Document Library</PageTitle>
        <p className={styles.sub}>
          {shelf === "campaign"
            ? "Upload rulebooks and notes — Quillbert answers from them."
            : "Your library: every one of your campaigns reads it."}
        </p>
      </header>
      <div className={styles.switch} role="tablist" aria-label="Which documents">
        {(
          [
            ["campaign", "This campaign"],
            ["library", "My library"],
          ] as const
        ).map(([id, label]) => (
          <button
            key={id}
            type="button"
            role="tab"
            aria-selected={shelf === id}
            className={shelf === id ? styles.tabActive : styles.tab}
            onClick={() => setShelf(id)}
          >
            {label}
          </button>
        ))}
      </div>
      {shelf === "campaign" ? (
        <DocumentLibrary source={{ campaignId: campaign.id }} focus={focus} />
      ) : (
        <DocumentLibrary source="library" defaultSystem={systemId} />
      )}
    </div>
  );
}
