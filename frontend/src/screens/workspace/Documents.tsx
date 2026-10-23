import type { Campaign } from "../../domains/campaign";
import { DocumentLibrary } from "../../domains/library";
import { PageTitle } from "../../ui/components";
import styles from "./Documents.module.css";

/** A document to scroll to and highlight, e.g. from a citation chip. */
export type DocumentFocus = { documentId: string; at: number };

export function Documents({ campaign, focus }: { campaign: Campaign; focus: DocumentFocus | null }) {
  return (
    <div className={styles.view}>
      <header className={styles.header}>
        <PageTitle>Document Library</PageTitle>
        <p className={styles.sub}>
          Upload rulebooks and notes — Quillbert answers from them.
        </p>
      </header>
      <DocumentLibrary campaignId={campaign.id} focus={focus} />
    </div>
  );
}
