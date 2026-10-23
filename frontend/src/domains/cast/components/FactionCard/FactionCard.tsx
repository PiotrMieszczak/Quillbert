import type { CSSProperties } from "react";
import { Badge } from "../../../../ui/components";
import { RELATIONSHIP_TONE, type Faction } from "../../model/types";
import styles from "./FactionCard.module.css";

export function FactionCard({ faction }: { faction: Faction }) {
  const tone = RELATIONSHIP_TONE[faction.relationship];
  return (
    <article className={styles.card} style={{ "--tone": tone } as CSSProperties}>
      <header className={styles.head}>
        <h3 className={styles.name}>{faction.name}</h3>
        <Badge tone={tone}>{faction.relationship}</Badge>
      </header>
      <p className={styles.type}>{faction.type}</p>
      {faction.motto && <blockquote className={styles.motto}>“{faction.motto}”</blockquote>}
      <dl className={styles.facts}>
        <div>
          <dt>Influence</dt>
          <dd>{faction.influence}</dd>
        </div>
        <div>
          <dt>Members</dt>
          <dd>{faction.memberCount}</dd>
        </div>
      </dl>
    </article>
  );
}
