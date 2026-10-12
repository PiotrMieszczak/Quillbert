import type { DocumentStatus, LibraryDocument } from "../../model/types";
import styles from "./DocumentRow.module.css";

const STATUS_TONE: Record<DocumentStatus, string> = {
  Indexed: "var(--success)",
  Processing: "var(--accent)",
  Queued: "var(--text-muted)",
};

export function DocumentRow({ document }: { document: LibraryDocument }) {
  const tone = STATUS_TONE[document.status];
  return (
    <li className={styles.row}>
      <span className={styles.thumb}>{document.kind}</span>
      <span className={styles.body}>
        <span className={styles.name}>{document.name}</span>
        <span className={styles.meta}>
          {document.pages === null ? document.meta : `${document.pages} pp · ${document.meta}`}
        </span>
      </span>
      <span className={styles.progress}>
        <span className={styles.statusLine}>
          <span className={styles.status} style={{ color: tone }}>
            {document.status}
          </span>
          <span className={styles.pct}>{document.progress}%</span>
        </span>
        <span
          className={styles.track}
          role="progressbar"
          aria-label={`${document.name} ${document.status.toLowerCase()}`}
          aria-valuenow={document.progress}
          aria-valuemin={0}
          aria-valuemax={100}
        >
          <span className={styles.fill} style={{ width: `${document.progress}%`, background: tone }} />
        </span>
      </span>
    </li>
  );
}
