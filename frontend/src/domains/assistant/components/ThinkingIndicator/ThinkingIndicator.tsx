import styles from "./ThinkingIndicator.module.css";

type ThinkingIndicatorProps = {
  /** The search step's label once the retrieval event has arrived. */
  searched?: string;
};

/** Shown until the first words of a reply arrive. Its steps follow the run's real events, never a script. */
export function ThinkingIndicator({ searched }: ThinkingIndicatorProps) {
  const steps = searched
    ? [
        { label: searched, done: true },
        { label: "Writing the answer", done: false },
      ]
    : [{ label: "Searching your documents", done: false }];

  return (
    <div className={styles.thinking} role="status" aria-live="polite">
      <div className={styles.head}>
        <div className={styles.tile} aria-hidden>
          <span className={styles.ring} />
          <img className={styles.quill} src="/quillbert-mark.svg" alt="" />
        </div>
        <div>
          <div className={styles.title}>Quillbert is reading</div>
          <svg className={styles.scribble} width="120" height="8" viewBox="0 0 120 8" aria-hidden>
            <path d="M2 5 C 14 1, 22 8, 34 4 S 56 1, 68 5 S 92 7, 104 3 L 118 4" />
          </svg>
        </div>
      </div>
      <ul className={styles.steps}>
        {steps.map((step) => (
          <li key={step.label} className={step.done ? styles.done : styles.active}>
            {step.done ? (
              <svg width="14" height="14" viewBox="0 0 14 14" fill="none" aria-hidden>
                <path className={styles.check} d="M2.5 7.2l3 3L11.5 4" />
              </svg>
            ) : (
              <span className={styles.spinner} aria-hidden />
            )}
            {step.label}
          </li>
        ))}
      </ul>
    </div>
  );
}
