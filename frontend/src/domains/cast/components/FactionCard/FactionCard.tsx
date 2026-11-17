import type { CSSProperties } from "react";
import { Badge } from "../../../../ui/components";
import { RELATIONSHIP_TONE, type Faction } from "../../model/types";
import styles from "./FactionCard.module.css";

/** With `onOpen` the card is one button into the faction's detail view. */
export function FactionCard({ faction, onOpen }: { faction: Faction; onOpen?: () => void }) {
  const tone = RELATIONSHIP_TONE[faction.relationship];
  const facts = [
    ["Influence", faction.influence],
    ["Reach", faction.reach],
  ].filter(([, value]) => value);
  return (
    <article className={styles.card} style={{ "--tone": tone } as CSSProperties}>
      <header className={styles.head}>
        <h3 className={styles.name}>
          {onOpen ? (
            // Its ::after covers the card, so the whole card opens the detail view.
            <button type="button" className={styles.open} onClick={onOpen}>
              {faction.name}
            </button>
          ) : (
            faction.name
          )}
        </h3>
        <Badge tone={tone}>{faction.relationship}</Badge>
      </header>
      {faction.type && <p className={styles.type}>{faction.type}</p>}
      {faction.motto && <blockquote className={styles.motto}>“{faction.motto}”</blockquote>}
      {facts.length > 0 && (
        <dl className={styles.facts}>
          {facts.map(([label, value]) => (
            <div key={label}>
              <dt>{label}</dt>
              <dd>{value}</dd>
            </div>
          ))}
        </dl>
      )}
    </article>
  );
}
