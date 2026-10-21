import type { Campaign } from "../../domains/campaign";
import { DocumentLibrary } from "../../domains/library";
import { PageTitle } from "../../ui/components";
import styles from "./Documents.module.css";

export function Documents({ campaign }: { campaign: Campaign }) {
  return (
    <div className={styles.view}>
      <header className={styles.header}>
        <PageTitle>Document Library</PageTitle>
        <p className={styles.sub}>
          Upload rulebooks and notes — Quillbert answers from them.
        </p>
      </header>
      <DocumentLibrary campaignId={campaign.id} />
    </div>
  );
}
