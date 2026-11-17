import { useState, type CSSProperties, type FormEvent, type ReactNode } from "react";
import { Badge, PageTitle } from "../../../../ui/components";
import { RELATIONSHIP_TONE, RELATIONSHIPS, type Relationship } from "../../model/types";
import { errorMessage } from "./errorMessage";
import styles from "./RecordPage.module.css";

type FieldProps = {
  label: string;
  value?: string;
  /** Present while editing. */
  onChange?: (value: string) => void;
  maxLength?: number;
  long?: boolean;
  required?: boolean;
  /** A custom control or value, in place of the text one. */
  children?: ReactNode;
};

/** A labelled value: text when read, an input when edited. */
export function Field({ label, value = "", onChange, maxLength = 120, long, required, children }: FieldProps) {
  const caption = (
    <span className={styles.label}>
      {label} {required && <span className={styles.required}>*</span>}
    </span>
  );
  if (children)
    return (
      <label className={styles.field}>
        {caption}
        {children}
      </label>
    );
  if (!onChange)
    return (
      <div className={styles.field}>
        {caption}
        <span className={long ? styles.prose : styles.value}>{value || "—"}</span>
      </div>
    );
  const props = { value, maxLength, required, onChange: (event: { target: { value: string } }) => onChange(event.target.value) };
  return (
    <label className={styles.field}>
      {caption}
      {long ? <textarea className={styles.textarea} rows={4} {...props} /> : <input className={styles.input} {...props} />}
    </label>
  );
}

/** A whole number, or null when left empty. */
export function NumberField(props: { label: string; value: number | null; onChange: (value: number | null) => void; min: number; max: number }) {
  const { label, value, onChange, min, max } = props;
  return (
    <Field label={label}>
      <input
        className={styles.input}
        type="number"
        min={min}
        max={max}
        step={1}
        value={value ?? ""}
        onChange={(event) => onChange(event.target.value === "" ? null : Number(event.target.value))}
      />
    </Field>
  );
}

export function RelationshipField({ value, onChange }: { value: Relationship; onChange: (value: Relationship) => void }) {
  return (
    <Field label="Relationship">
      <select className={styles.input} value={value} onChange={(event) => onChange(event.target.value as Relationship)}>
        {RELATIONSHIPS.map((option) => (
          <option key={option} value={option}>
            {option}
          </option>
        ))}
      </select>
    </Field>
  );
}

type SectionProps = {
  label: string;
  /** Show the label as the card's heading. */
  title?: boolean;
  /** Lay the children out in columns. */
  grid?: boolean;
  /** Full-width content under the grid. */
  footer?: ReactNode;
  children: ReactNode;
};

/** A card of the page. */
export function Section({ label, title, grid, footer, children }: SectionProps) {
  return (
    <section className={styles.card} aria-label={label}>
      {title && <h2 className={styles.title}>{label}</h2>}
      {grid ? <div className={styles.grid}>{children}</div> : children}
      {footer}
    </section>
  );
}

type RecordPageProps = {
  /** The list this page was opened from, for the back link. */
  listLabel: string;
  title: string;
  relationship: Relationship;
  editing: boolean;
  busy: boolean;
  /** Save stays disabled until the record is valid. */
  canSave: boolean;
  saveLabel: string;
  error: string | null;
  onClose: () => void;
  onSave: () => void;
  onCancel: () => void;
  onEdit: () => void;
  onRemove: () => void;
  children: ReactNode;
};

/** The frame of a character or faction page: back link, title, and the Edit / Save / Delete
 *  actions, with Delete turning into Remove / Keep before anything is deleted. */
export function RecordPage(props: RecordPageProps) {
  const { listLabel, title, relationship, editing, busy, canSave, saveLabel, error, children } = props;
  const [confirming, setConfirming] = useState(false);
  const tone = RELATIONSHIP_TONE[relationship];
  const submit = (event: FormEvent) => {
    event.preventDefault();
    if (editing) props.onSave();
  };
  return (
    <form className={styles.page} onSubmit={submit} style={{ "--tone": tone } as CSSProperties}>
      <button type="button" className={styles.back} onClick={props.onClose}>
        ← {listLabel}
      </button>
      <header className={styles.header}>
        <div className={styles.heading}>
          <PageTitle>{title}</PageTitle>
          {!editing && <Badge tone={tone}>{relationship}</Badge>}
        </div>
        <div className={styles.actions}>
          {editing ? (
            <>
              <button type="button" className={styles.ghost} onClick={props.onCancel} disabled={busy}>
                Cancel
              </button>
              <button type="submit" className={styles.primary} disabled={busy || !canSave}>
                {busy ? "Saving…" : saveLabel}
              </button>
            </>
          ) : confirming ? (
            <>
              <button type="button" className={styles.danger} onClick={props.onRemove} disabled={busy}>
                Remove
              </button>
              <button type="button" className={styles.ghost} onClick={() => setConfirming(false)} disabled={busy}>
                Keep
              </button>
            </>
          ) : (
            <>
              <button type="button" className={styles.ghost} onClick={() => setConfirming(true)}>
                Delete
              </button>
              <button type="button" className={styles.primary} onClick={props.onEdit}>
                Edit
              </button>
            </>
          )}
        </div>
      </header>
      {error && (
        <p className={styles.error} role="alert">
          {error}
        </p>
      )}
      {children}
    </form>
  );
}

/** Shown in place of a page whose record is loading or failed to load. */
export function RecordMessage({ listLabel, onClose, error }: { listLabel: string; onClose: () => void; error: unknown }) {
  return (
    <div className={styles.page}>
      <button type="button" className={styles.back} onClick={onClose}>
        ← {listLabel}
      </button>
      <p className={styles.message} role={error ? "alert" : undefined}>
        {error ? `Could not load. ${errorMessage(error)}` : "Loading…"}
      </p>
    </div>
  );
}
