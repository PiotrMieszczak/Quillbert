import type { CSSProperties } from "react";
import { Badge } from "../../../../ui/components";
import { RELATIONSHIP_TONE, type Character } from "../../model/types";
import styles from "./CharacterCard.module.css";

/** NPC or player-character card. A player character shows its player and class line. */
export function CharacterCard({ character }: { character: Character }) {
  const { player } = character;
  const level = character.level != null ? `Level ${character.level}` : null;
  const meta = player
    ? [player.playerName && `Played by ${player.playerName}`, level].filter(Boolean)
    : [level, character.location].filter(Boolean);
  return (
    <article className={styles.card} style={{ "--tone": RELATIONSHIP_TONE[character.relationship] } as CSSProperties}>
      <div className={styles.portrait} aria-hidden>
        {character.name.charAt(0)}
      </div>
      <div className={styles.body}>
        <h3 className={styles.name}>{character.name}</h3>
        <p className={styles.role}>{player ? `${player.race} ${player.class}` : character.role}</p>
        {meta.length > 0 && <p className={styles.meta}>{meta.join(" · ")}</p>}
        {character.tags.length > 0 && (
          <div className={styles.tags}>
            {character.tags.map((tag) => (
              <Badge key={tag}>{tag}</Badge>
            ))}
          </div>
        )}
      </div>
    </article>
  );
}
