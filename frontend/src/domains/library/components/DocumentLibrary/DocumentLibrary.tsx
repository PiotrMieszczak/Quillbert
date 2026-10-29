import { useQueryClient } from "@tanstack/react-query";
import { useRef, useState } from "react";
import { useSystems } from "../../../campaign";
import {
  deleteDocument,
  documentsKey,
  type DocumentSource,
  type UploadTags,
  uploadDocument,
  useDocuments,
} from "../../api/documents";
import { pendingFromFile } from "../../model/queued";
import type { LibraryDocument } from "../../model/types";
import { DocumentRow } from "../DocumentRow";
import { type StagedFile, UploadReview } from "../UploadReview";
import { UploadZone } from "../UploadZone";
import styles from "./DocumentLibrary.module.css";

type DocumentLibraryProps = {
  /** A campaign's documents, or the GM's library (ADR-0027). */
  source: DocumentSource;
  /** System id new library uploads start on, e.g. the campaign's; none means every system. */
  defaultSystem?: string;
  /** Scroll to and flash this document, or with no document focus the upload zone; `at` changes on
   *  every request, so a repeat flashes again. */
  focus?: { documentId?: string; at: number } | null;
};

export function DocumentLibrary({ source, defaultSystem = "", focus }: DocumentLibraryProps) {
  const documents = useDocuments(source);
  const systems = useSystems();
  // Library files wait here for their system (ADR-0027); campaign files upload at once.
  const [staged, setStaged] = useState<StagedFile[]>([]);
  const shared = typeof source === "string";
  const queryClient = useQueryClient();
  // Files the API has not accepted yet: in flight, or refused with the server's reason.
  const [pending, setPending] = useState<LibraryDocument[]>([]);
  const uploads = useRef(new Map<string, AbortController>());
  const [notice, setNotice] = useState<string | null>(null);
  const [failure, setFailure] = useState<string | null>(null);

  const dismiss = (id: string) => setPending((rows) => rows.filter((row) => row.id !== id));
  const refresh = () => queryClient.invalidateQueries({ queryKey: documentsKey(source) });

  function stage(files: File[]) {
    const fresh = files.map((file) => ({ id: crypto.randomUUID(), file, system: defaultSystem }));
    setStaged((rows) => [...rows, ...fresh]);
  }

  function uploadStaged() {
    staged.forEach(({ file, system }) => void upload(file, { systems: system ? [system] : [] }));
    setStaged([]);
  }

  async function upload(file: File, tags: UploadTags = {}) {
    const id = crypto.randomUUID();
    const controller = new AbortController();
    uploads.current.set(id, controller);
    setPending((rows) => [...rows, pendingFromFile(file, id)]);
    try {
      const { document, duplicate } = await uploadDocument(source, file, tags, controller.signal);
      if (duplicate) {
        const as = document.name === file.name ? "" : ` as “${document.name}”`;
        setNotice(`“${file.name}” is already in the library${as}.`);
      }
      // Refetch first, so the accepted row replaces the pending one without a gap.
      await refresh();
      dismiss(id);
    } catch (error) {
      if (controller.signal.aborted) return; // cancelled: its row is already gone
      const reason = error instanceof Error ? error.message : "Upload failed.";
      setPending((rows) => rows.map((row) => (row.id === id ? pendingFromFile(file, id, reason) : row)));
    } finally {
      uploads.current.delete(id);
    }
  }

  function cancel(id: string) {
    uploads.current.get(id)?.abort();
    dismiss(id);
  }

  async function remove(document: LibraryDocument) {
    setFailure(null);
    try {
      await deleteDocument(source, document.id);
      await refresh();
    } catch (error) {
      const reason = error instanceof Error ? error.message : "Something went wrong.";
      setFailure(`Couldn’t remove “${document.name}”: ${reason}`);
    }
  }

  const rows = documents.data ?? [];

  return (
    <div className={styles.library}>
      <UploadZone
        focusAt={focus && !focus.documentId ? focus.at : undefined}
        onFiles={(files) => {
          setNotice(null);
          if (shared) stage(files);
          else files.forEach((file) => void upload(file));
        }}
      />
      {staged.length > 0 && (
        <UploadReview
          files={staged}
          systems={systems.data ?? []}
          onChange={(id, patch) => setStaged((rows) => rows.map((row) => (row.id === id ? { ...row, ...patch } : row)))}
          onRemove={(id) => setStaged((rows) => rows.filter((row) => row.id !== id))}
          onCancel={() => setStaged([])}
          onUpload={uploadStaged}
        />
      )}

      {notice && (
        <p className={styles.notice} role="status">
          {notice}
        </p>
      )}
      {failure && (
        <p className={styles.error} role="alert">
          {failure}
        </p>
      )}
      {documents.isPending && (
        <p className={styles.message} role="status">
          Loading documents…
        </p>
      )}
      {documents.isError && (
        <p className={styles.error} role="alert">
          Couldn’t load the library: {documents.error.message}{" "}
          <button type="button" className={styles.retry} onClick={() => void documents.refetch()}>
            Try again
          </button>
        </p>
      )}
      {documents.isSuccess && rows.length === 0 && pending.length === 0 && (
        <p className={styles.message}>No documents yet. Drop a rulebook, module, or your notes above.</p>
      )}

      {(rows.length > 0 || pending.length > 0) && (
        <ul className={styles.list}>
          {rows.map((document) => (
            <DocumentRow
              key={document.id}
              document={document}
              tags={document.systems.map((id) => systems.data?.find((system) => system.id === id)?.name ?? id)}
              flash={focus?.documentId === document.id ? focus.at : undefined}
              onRemove={() => remove(document)}
            />
          ))}
          {pending.map((document) => (
            <DocumentRow
              key={document.id}
              document={document}
              onCancel={document.status === "Uploading" ? () => cancel(document.id) : undefined}
              onDismiss={document.status === "Failed" ? () => dismiss(document.id) : undefined}
            />
          ))}
        </ul>
      )}
    </div>
  );
}

