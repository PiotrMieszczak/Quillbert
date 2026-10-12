import { useState } from "react";
import styles from "./UploadZone.module.css";

// By extension: browsers report MIME types for .md and .docx inconsistently, often as "".
const ACCEPTED = [".pdf", ".md", ".txt", ".docx"];

const isAccepted = (file: File) =>
  ACCEPTED.some((extension) => file.name.toLowerCase().endsWith(extension));

type UploadZoneProps = {
  onFiles: (files: File[]) => void;
};

/** The whole zone is a label for the hidden input, so a click anywhere opens the picker.
 *  Dropped files skip the input's `accept`, so they are filtered here. */
export function UploadZone({ onFiles }: UploadZoneProps) {
  const [dragging, setDragging] = useState(false);

  return (
    <label
      className={[styles.zone, dragging && styles.dragging].filter(Boolean).join(" ")}
      onDragOver={(event) => {
        event.preventDefault();
        setDragging(true);
      }}
      onDragLeave={(event) => {
        if (!event.currentTarget.contains(event.relatedTarget as Node | null)) setDragging(false);
      }}
      onDrop={(event) => {
        event.preventDefault();
        setDragging(false);
        const files = Array.from(event.dataTransfer.files).filter(isAccepted);
        if (files.length) onFiles(files);
      }}
    >
      <input
        type="file"
        multiple
        accept={ACCEPTED.join(",")}
        className={styles.input}
        onChange={(event) => {
          onFiles(Array.from(event.target.files ?? []));
          event.target.value = "";
        }}
      />
      <span className={styles.icon} aria-hidden>
        <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6">
          <path
            d="M12 16V4m0 0L8 8m4-4l4 4M4 16v2a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-2"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
      </span>
      <span className={styles.text}>
        <span className={styles.title}>Drop rulebooks or adventure modules</span>
        <span className={styles.hint}>PDF, Markdown, text, DOCX · bulk upload supported · ~3s/page</span>
      </span>
      <span className={styles.button} aria-hidden>
        Browse files
      </span>
    </label>
  );
}
