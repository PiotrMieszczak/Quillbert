import type { GameSystem } from "../../../campaign";
import styles from "./UploadReview.module.css";

/** A dropped file waiting for its system. `system` is a system id; "" means every system. */
export type StagedFile = { id: string; file: File; system: string };

type UploadReviewProps = {
  files: StagedFile[];
  systems: GameSystem[];
  onChange: (id: string, patch: Partial<StagedFile>) => void;
  onRemove: (id: string) => void;
  onCancel: () => void;
  onUpload: () => void;
};

/** Library uploads ask, per file, which system it applies to (ADR-0027).
 *  A campaign upload never stops here. */
export function UploadReview({ files, systems, onChange, onRemove, onCancel, onUpload }: UploadReviewProps) {
  const count = files.length === 1 ? "1 file" : `${files.length} files`;

  return (
    <section className={styles.review} aria-label="Review upload">
      <header className={styles.header}>
        <span className={styles.heading}>
          <span className={styles.title}>Add {count}</span>
          <span className={styles.hint}>Each file applies to every system unless you pick one.</span>
        </span>
        {files.length > 1 && (
          <label className={styles.setAll}>
            <span className={styles.eyebrow}>Set all</span>
            <SystemSelect
              systems={systems}
              value={files.every((f) => f.system === files[0].system) ? files[0].system : null}
              onChange={(system) => files.forEach((f) => onChange(f.id, { system }))}
            />
          </label>
        )}
      </header>

      <ul className={styles.list}>
        {files.map((staged) => (
          <li key={staged.id} className={styles.row}>
            <span className={styles.name} title={staged.file.name}>
              {staged.file.name}
            </span>
            <SystemSelect
              label={`System for ${staged.file.name}`}
              systems={systems}
              value={staged.system}
              onChange={(system) => onChange(staged.id, { system })}
            />
            <button
              type="button"
              className={styles.remove}
              aria-label={`Don’t upload ${staged.file.name}`}
              onClick={() => onRemove(staged.id)}
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden>
                <path d="M6 6l12 12M18 6L6 18" strokeLinecap="round" />
              </svg>
            </button>
          </li>
        ))}
      </ul>

      <footer className={styles.footer}>
        <button type="button" className={styles.ghost} onClick={onCancel}>
          Cancel
        </button>
        <button type="button" className={styles.primary} onClick={onUpload}>
          Upload {count}
        </button>
      </footer>
    </section>
  );
}

type SystemSelectProps = {
  systems: GameSystem[];
  /** null: the files disagree (for "Set all"). */
  value: string | null;
  onChange: (system: string) => void;
  label?: string;
};

function SystemSelect({ systems, value, onChange, label }: SystemSelectProps) {
  return (
    <select
      className={styles.select}
      aria-label={label}
      value={value ?? "mixed"}
      onChange={(event) => onChange(event.target.value)}
    >
      {value === null && (
        <option value="mixed" disabled>
          Mixed
        </option>
      )}
      <option value="">All systems</option>
      {systems.map((system) => (
        <option key={system.id} value={system.id}>
          {system.name}
        </option>
      ))}
    </select>
  );
}
