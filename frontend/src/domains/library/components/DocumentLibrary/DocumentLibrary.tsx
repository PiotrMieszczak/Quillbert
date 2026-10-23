import { useQueryClient } from "@tanstack/react-query";
import { useRef, useState } from "react";
import { useSystems } from "../../../campaign";
import {
  deleteDocument,
  documentsKey,
  type DocumentSource,
  uploadDocument,
  useDocuments,
} from "../../api/documents";
import { pendingFromFile } from "../../model/queued";
import type { LibraryDocument } from "../../model/types";
import { DocumentRow } from "../DocumentRow";
import { UploadZone } from "../UploadZone";
import styles from "./DocumentLibrary.module.css";

type DocumentLibraryProps = {
  /** A campaign's documents, the GM's library, or the vault (ADR-0027). */
  source: DocumentSource;
  /** List only: no upload and no remove (the vault, for a GM who is not the admin). */
  readOnly?: boolean;
  /** Scroll to and flash this document; `at` changes on every request, so a repeat flashes again. */
  focus?: { documentId: string; at: number } | null;
};

export function DocumentLibrary({ source, readOnly = false, focus }: DocumentLibraryProps) {
  const documents = useDocuments(source);
  const shared = typeof source === "string";
  // Tags for the next library or vault upload: no systems means every system.
  const [systems, setSystems] = useState<string[]>([]);
  const [attribution, setAttribution] = useState("");
  const queryClient = useQueryClient();
  // Files the API has not accepted yet: in flight, or refused with the server's reason.
  const [pending, setPending] = useState<LibraryDocument[]>([]);
  const uploads = useRef(new Map<string, AbortController>());
  const [notice, setNotice] = useState<string | null>(null);
  const [failure, setFailure] = useState<string | null>(null);

  const dismiss = (id: string) => setPending((rows) => rows.filter((row) => row.id !== id));
  const refresh = () => queryClient.invalidateQueries({ queryKey: documentsKey(source) });

  async function upload(file: File) {
    const id = crypto.randomUUID();
    const controller = new AbortController();
    uploads.current.set(id, controller);
    setPending((rows) => [...rows, pendingFromFile(file, id)]);
    try {
      const tags = { systems, attribution: attribution.trim() };
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
      {shared && !readOnly && (
        <ShelfTags
          vault={source === "vault"}
          systems={systems}
          onSystems={setSystems}
          attribution={attribution}
          onAttribution={setAttribution}
        />
      )}
      {!readOnly && (
        <UploadZone
          onFiles={(files) => {
            setNotice(null);
            files.forEach((file) => void upload(file));
          }}
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
              flash={focus?.documentId === document.id ? focus.at : undefined}
              onRemove={readOnly ? undefined : () => remove(document)}
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

type ShelfTagsProps = {
  vault: boolean;
  systems: string[];
  onSystems: (systems: string[]) => void;
  attribution: string;
  onAttribution: (attribution: string) => void;
};

/** What the next upload applies to. Shown on the library and the vault, not on a campaign. */
function ShelfTags({ vault, systems, onSystems, attribution, onAttribution }: ShelfTagsProps) {
  const known = useSystems();
  const toggle = (id: string) =>
    onSystems(systems.includes(id) ? systems.filter((s) => s !== id) : [...systems, id]);

  return (
    <div className={styles.tags}>
      <fieldset className={styles.systems}>
        <legend className={styles.legend}>Applies to</legend>
        {known.data?.map((system) => (
          <label key={system.id} className={styles.check}>
            <input type="checkbox" checked={systems.includes(system.id)} onChange={() => toggle(system.id)} />
            {system.name}
          </label>
        ))}
        <span className={styles.hint}>{systems.length === 0 ? "None ticked: every system." : ""}</span>
      </fieldset>
      {vault && (
        <label className={styles.attribution}>
          <span className={styles.legend}>Attribution</span>
          <input
            type="text"
            value={attribution}
            placeholder="e.g. SRD 5.2 · CC-BY-4.0"
            onChange={(event) => onAttribution(event.target.value)}
          />
        </label>
      )}
    </div>
  );
}
