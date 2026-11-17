import { useId, useState, type ChangeEvent, type CSSProperties, type FormEvent, type ReactNode } from "react";
import { RELATIONSHIP_TONE, RELATIONSHIPS, type Relationship } from "../../model/types";
import styles from "./RecordPage.module.css";

type FieldProps = {
  label: string;
  value: string;
  onChange: (value: string) => void;
  maxLength?: number;
  placeholder?: string;
};

/** One line of a panel: the label beside a value that is typed over in place. */
export function Row({ label, value, onChange, maxLength = 120, placeholder = "—" }: FieldProps) {
  return (
    <label className={styles.row}>
      <span className={styles.label}>{label}</span>
      {/* A textarea so a long value wraps instead of being cut off. */}
      <textarea
        className={styles.quiet}
        rows={1}
        value={value}
        maxLength={maxLength}
        placeholder={placeholder}
        onChange={(event) => onChange(event.target.value.replace(/\n/g, " "))}
      />
    </label>
  );
}

/** A whole number beside its label, or null when left empty. */
export function NumberRow(props: { label: string; value: number | null; onChange: (value: number | null) => void; min: number; max: number }) {
  const { label, value, onChange, min, max } = props;
  return (
    <label className={styles.row}>
      <span className={styles.label}>{label}</span>
      <input
        className={styles.quiet}
        type="number"
        inputMode="numeric"
        min={min}
        max={max}
        step={1}
        value={value ?? ""}
        placeholder="—"
        onChange={(event) => onChange(event.target.value === "" ? null : Number(event.target.value))}
      />
    </label>
  );
}

/** Longer writing: the label above text that grows with what is typed. */
export function Prose({ label, value, onChange, maxLength = 2000, placeholder }: FieldProps) {
  return (
    <label className={styles.prose}>
      <span className={styles.label}>{label}</span>
      <textarea
        className={styles.quiet}
        rows={2}
        value={value}
        maxLength={maxLength}
        placeholder={placeholder ?? "—"}
        onChange={(event) => onChange(event.target.value)}
      />
    </label>
  );
}

/** A titled block of the page. `note` sits beside the title, e.g. "Private". */
export function Panel({ title, note, children }: { title: string; note?: string; children: ReactNode }) {
  return (
    <section className={styles.panel} aria-label={title}>
      <h2 className={styles.title}>
        {title}
        {note && <span className={styles.note}>{note}</span>}
      </h2>
      {children}
    </section>
  );
}

type RecordPageProps = {
  /** The list this page was opened from, for the back link. */
  listLabel: string;
  name: string;
  onName: (value: string) => void;
  namePlaceholder: string;
  /** The line under the name: a character's role, a faction's type. */
  subtitle: string;
  onSubtitle: (value: string) => void;
  subtitlePlaceholder: string;
  relationship: Relationship;
  onRelationship: (value: Relationship) => void;
  /** A record that can carry a picture: what to show, the types to offer, and what to do with a
   *  picked file. Without it the tile shows the name's initial. */
  portrait?: { src: string | null; accept: string[]; onPick: (file: File) => void };
  /** Not saved yet: there is nothing to delete, and the bar offers Create. */
  isNew: boolean;
  /** Something was typed since the last save. */
  dirty: boolean;
  busy: boolean;
  /** Save stays disabled until the record is valid. */
  canSave: boolean;
  saveLabel: string;
  error: string | null;
  onClose: () => void;
  onSave: () => void;
  onDiscard: () => void;
  onRemove: () => void;
  /** The narrow column: facts about the record. */
  side: ReactNode;
  /** The wide column: what the GM reads at the table. */
  children: ReactNode;
};

/** The frame of a character or faction page. Every value is typed over in place, like a paper
 *  sheet; nothing is saved until the bar that appears with the first change says so. */
export function RecordPage(props: RecordPageProps) {
  const { listLabel, name, relationship, isNew, dirty, busy, canSave, error } = props;
  const [confirming, setConfirming] = useState(false);
  const submit = (event: FormEvent) => {
    event.preventDefault();
    if (dirty && canSave && !busy) props.onSave();
  };
  const back = () => {
    // A new record with nothing typed has nothing to lose.
    if (dirty && (!isNew || name.trim() !== "") && !window.confirm("Leave without saving your changes?")) return;
    props.onClose();
  };
  return (
    <form className={styles.page} onSubmit={submit} style={{ "--tone": RELATIONSHIP_TONE[relationship] } as CSSProperties}>
      <BackLink label={listLabel} onClick={back} />
      <header className={styles.hero}>
        <Portrait initial={name.trim().charAt(0) || "?"} picture={props.portrait} />
        <div className={styles.identity}>
          <input
            className={styles.name}
            value={name}
            maxLength={120}
            required
            placeholder={props.namePlaceholder}
            aria-label="Name"
            // A new record starts with the cursor in its name.
            autoFocus={isNew}
            onChange={(event) => props.onName(event.target.value)}
          />
          <input
            className={styles.subtitle}
            value={props.subtitle}
            maxLength={120}
            placeholder={props.subtitlePlaceholder}
            aria-label={props.subtitlePlaceholder}
            onChange={(event) => props.onSubtitle(event.target.value)}
          />
        </div>
        <div className={styles.heroActions}>
          <label className={styles.relationship}>
            <span className={styles.dot} aria-hidden />
            <select
              value={relationship}
              aria-label="Relationship to the party"
              onChange={(event) => props.onRelationship(event.target.value as Relationship)}
            >
              {RELATIONSHIPS.map((option) => (
                <option key={option} value={option}>
                  {option.charAt(0).toUpperCase() + option.slice(1)}
                </option>
              ))}
            </select>
          </label>
          {!isNew &&
            (confirming ? (
              <>
                <button type="button" className={styles.danger} onClick={props.onRemove} disabled={busy}>
                  Remove
                </button>
                <button type="button" className={styles.ghost} onClick={() => setConfirming(false)} disabled={busy}>
                  Keep
                </button>
              </>
            ) : (
              <button type="button" className={styles.ghost} onClick={() => setConfirming(true)}>
                Delete
              </button>
            ))}
        </div>
      </header>

      <div className={styles.layout}>
        <div className={styles.main}>{props.children}</div>
        <aside className={styles.side}>{props.side}</aside>
      </div>

      {(dirty || error) && (
        <div className={styles.saveBar} role="status">
          <p className={error ? styles.error : styles.status}>{error ?? (isNew ? "Not saved yet" : "Unsaved changes")}</p>
          <button type="button" className={styles.ghost} onClick={isNew ? props.onClose : props.onDiscard} disabled={busy}>
            {isNew ? "Cancel" : "Discard"}
          </button>
          <button type="submit" className={styles.primary} disabled={busy || !dirty || !canSave}>
            {busy ? "Saving…" : props.saveLabel}
          </button>
        </div>
      )}
    </form>
  );
}

type PortraitProps = { initial: string; picture: RecordPageProps["portrait"] };

/** The picture tile. With a `picture` it is a file picker: click or drop an image on it. */
function Portrait({ initial, picture }: PortraitProps) {
  const inputId = useId();
  if (!picture)
    return (
      <div className={styles.portrait} aria-hidden>
        {initial}
      </div>
    );
  const pick = (event: ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    event.target.value = ""; // picking the same file again still fires change
    if (file) picture.onPick(file);
  };
  return (
    <label
      htmlFor={inputId}
      className={styles.portraitPicker}
      title={picture.src ? "Change portrait" : "Add a portrait"}
      onDragOver={(event) => event.preventDefault()}
      onDrop={(event) => {
        event.preventDefault();
        const file = event.dataTransfer.files[0];
        if (file) picture.onPick(file);
      }}
    >
      {picture.src ? <img src={picture.src} alt="" /> : <span aria-hidden>{initial}</span>}
      <span className={styles.portraitHint} aria-hidden>
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M12 16V5m0 0L8 9m4-4l4 4M5 16v2a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2v-2" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
      </span>
      <input
        id={inputId}
        className={styles.fileInput}
        type="file"
        accept={picture.accept.join(",")}
        aria-label={picture.src ? "Change portrait" : "Add a portrait"}
        onChange={pick}
      />
    </label>
  );
}

function BackLink({ label, onClick }: { label: string; onClick: () => void }) {
  return (
    <button type="button" className={styles.back} onClick={onClick}>
      <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="1.7" aria-hidden>
        <path d="M8.5 3L4.5 7l4 4" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
      {label}
    </button>
  );
}

/** Shown in place of a page whose record is loading or failed to load. */
export function RecordMessage({ listLabel, onClose, error }: { listLabel: string; onClose: () => void; error: string | null }) {
  return (
    <div className={styles.page}>
      <BackLink label={listLabel} onClick={onClose} />
      <p className={styles.message} role={error ? "alert" : undefined}>
        {error ? `Could not load. ${error}` : "Loading…"}
      </p>
    </div>
  );
}
