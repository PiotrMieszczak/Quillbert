import type { DocumentStatus, LibraryDocument } from "../../model/types";
import styles from "./DocumentRow.module.css";

const STATUS_TONE: Record<DocumentStatus, string> = {
  Indexed: "var(--success)",
  Processing: "var(--accent)",
  Queued: "var(--text-muted)",
  Uploading: "var(--accent)",
  Failed: "var(--rel-enemy)",
};

type DocumentRowProps = {
  document: LibraryDocument;
  /** Shown for a refused upload, so the user can clear it. */
  onDismiss?: () => void;
};

export function DocumentRow({ document, onDismiss }: DocumentRowProps) {
  const tone = STATUS_TONE[document.status];
  const failed = document.status === "Failed";
  return (
    <li className={styles.row}>
      <span className={styles.thumb}>{document.kind}</span>
      <span className={styles.body}>
        <span className={styles.name}>{document.name}</span>
        <span className={failed ? styles.metaError : styles.meta}>
          {document.pages === null ? document.meta : `${document.pages} pp · ${document.meta}`}
        </span>
      </span>
      <span className={styles.progress}>
        <span className={styles.statusLine}>
          <span className={styles.status} style={{ color: tone }}>
            {document.status}
          </span>
          {document.status !== "Uploading" && !failed && <span className={styles.pct}>{document.progress}%</span>}
        </span>
        <span
          className={styles.track}
          role="progressbar"
          aria-label={`${document.name} ${document.status.toLowerCase()}`}
          aria-valuenow={document.progress}
          aria-valuemin={0}
          aria-valuemax={100}
        >
          <span className={styles.fill} style={{ width: failed ? "100%" : `${document.progress}%`, background: tone }} />
        </span>
      </span>
      {onDismiss && (
        <button type="button" className={styles.dismiss} aria-label={`Dismiss ${document.name}`} onClick={onDismiss}>
          ×
        </button>
      )}
    </li>
  );
}
