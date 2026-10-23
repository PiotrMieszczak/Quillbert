import { FACTIONS, FactionCard } from "../../domains/cast";
import { Badge, PageTitle } from "../../ui/components";
import styles from "./Cast.module.css";

export function Factions() {
  return (
    <div className={styles.view}>
      <header className={styles.header}>
        <div className={styles.heading}>
          <PageTitle>Factions</PageTitle>
          <p className={styles.sub}>The powers in play and where the party stands with each.</p>
        </div>
        <Badge>Sample data</Badge>
      </header>
      <ul className={styles.grid}>
        {FACTIONS.map((faction) => (
          <li key={faction.id}>
            <FactionCard faction={faction} />
          </li>
        ))}
      </ul>
    </div>
  );
}
