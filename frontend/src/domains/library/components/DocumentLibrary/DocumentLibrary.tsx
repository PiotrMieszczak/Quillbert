import { useState } from "react";
import { DOCUMENTS } from "../../model/fixtures";
import { queuedFromFile } from "../../model/queued";
import { DocumentRow } from "../DocumentRow";
import { UploadZone } from "../UploadZone";
import styles from "./DocumentLibrary.module.css";

export function DocumentLibrary() {
  // shortcut: local state over fixtures; becomes a TanStack Query hook once #21 serves documents.
  const [documents, setDocuments] = useState(DOCUMENTS);

  const addFiles = (files: File[]) =>
    setDocuments((current) => [
      ...current,
      ...files.map((file) => queuedFromFile(file, crypto.randomUUID())),
    ]);

  return (
    <div className={styles.library}>
      <UploadZone onFiles={addFiles} />
      <ul className={styles.list}>
        {documents.map((document) => (
          <DocumentRow key={document.id} document={document} />
        ))}
      </ul>
    </div>
  );
}
