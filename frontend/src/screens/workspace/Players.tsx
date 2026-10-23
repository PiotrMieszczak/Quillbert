import { CharacterCard, PLAYERS } from "../../domains/cast";
import { Badge, PageTitle } from "../../ui/components";
import styles from "./Cast.module.css";

export function Players() {
  return (
    <div className={styles.view}>
      <header className={styles.header}>
        <div className={styles.heading}>
          <PageTitle>Party</PageTitle>
          <p className={styles.sub}>The player characters and who plays them.</p>
        </div>
        <div className={styles.actions}>
          <Badge>Sample data</Badge>
          {/* shortcut: the Add Player form is not built yet; enabled when the cast API lands. */}
          <button type="button" className={styles.add} disabled title="Coming soon">
            Add Player
          </button>
        </div>
      </header>
      <ul className={styles.grid}>
        {PLAYERS.map((player) => (
          <li key={player.id}>
            <CharacterCard character={player} />
          </li>
        ))}
      </ul>
    </div>
  );
}
