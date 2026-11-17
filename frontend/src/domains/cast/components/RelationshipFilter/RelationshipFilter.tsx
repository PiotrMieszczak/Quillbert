import { RELATIONSHIP_TONE, RELATIONSHIPS, type Relationship } from "../../model/types";
import styles from "./RelationshipFilter.module.css";

const LABELS: Record<Relationship, string> = {
  ally: "Allies",
  enemy: "Enemies",
  family: "Family",
  professional: "Pro",
  neutral: "Neutral",
};

type RelationshipFilterProps = {
  value: Relationship | null;
  onChange: (value: Relationship | null) => void;
};

/** All / Allies / Enemies / Family / Pro / Neutral chips; null means All. */
export function RelationshipFilter({ value, onChange }: RelationshipFilterProps) {
  const options: (Relationship | null)[] = [null, ...RELATIONSHIPS];
  return (
    <div className={styles.chips} role="group" aria-label="Filter by relationship">
      {options.map((option) => (
        <button
          key={option ?? "all"}
          type="button"
          className={styles.chip}
          aria-pressed={value === option}
          onClick={() => onChange(option)}
        >
          {option && <span className={styles.dot} style={{ color: RELATIONSHIP_TONE[option] }} aria-hidden />}
          {option ? LABELS[option] : "All"}
        </button>
      ))}
    </div>
  );
}
