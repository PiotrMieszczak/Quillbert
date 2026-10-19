import { useState } from "react";
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
  /** A refused upload: clear the row. */
  onDismiss?: () => void;
  /** An upload in flight: stop it. */
  onCancel?: () => void;
  /** A stored document: delete it and its file, after the user confirms. */
  onRemove?: () => Promise<void>;
};

export function DocumentRow({ document, onDismiss, onCancel, onRemove }: DocumentRowProps) {
  const [confirming, setConfirming] = useState(false);
  const [removing, setRemoving] = useState(false);
  const tone = STATUS_TONE[document.status];
  const failed = document.status === "Failed";

  async function remove() {
    setRemoving(true);
    try {
      await onRemove?.();
    } finally {
      setRemoving(false);
      setConfirming(false);
    }
  }

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

      {onCancel && (
        <button type="button" className={styles.action} onClick={onCancel}>
          Cancel
        </button>
      )}
      {onDismiss && (
        <button type="button" className={styles.icon} aria-label={`Dismiss ${document.name}`} onClick={onDismiss}>
          ×
        </button>
      )}
      {onRemove && !confirming && (
        <button
          type="button"
          className={styles.icon}
          aria-label={`Remove ${document.name}`}
          title="Remove"
          onClick={() => setConfirming(true)}
        >
          <TrashGlyph />
        </button>
      )}
      {onRemove && confirming && (
        <span className={styles.confirm}>
          <button type="button" className={styles.danger} disabled={removing} onClick={() => void remove()}>
            {removing ? "Removing…" : "Remove"}
          </button>
          <button type="button" className={styles.action} disabled={removing} onClick={() => setConfirming(false)}>
            Keep
          </button>
        </span>
      )}
    </li>
  );
}

function TrashGlyph() {
  return (
    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M4 7h16M10 11v6M14 11v6M6 7l1 12a2 2 0 0 0 2 2h6a2 2 0 0 0 2-2l1-12M9 7V4h6v3" />
    </svg>
  );
}
