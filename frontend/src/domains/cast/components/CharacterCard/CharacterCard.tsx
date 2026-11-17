import type { CSSProperties } from "react";
import { Badge } from "../../../../ui/components";
import { usePortrait } from "../../api/characters";
import { RELATIONSHIP_TONE, type Character } from "../../model/types";
import styles from "./CharacterCard.module.css";

/** NPC or player-character card. A player character shows its player and class line.
 *  With `onOpen` the card is one button into the character's detail view. */
export function CharacterCard({ character, onOpen }: { character: Character; onOpen?: () => void }) {
  const { player } = character;
  const portrait = usePortrait(character.portraitUrl).data;
  const level = character.level != null ? `Level ${character.level}` : null;
  const meta = player
    ? [player.playerName && `Played by ${player.playerName}`, level].filter(Boolean)
    : [level, character.location].filter(Boolean);
  // A player with an empty profile falls back to the character's own role.
  const role = (player && [player.race, player.class].filter(Boolean).join(" ")) || character.role;
  return (
    <article className={styles.card} style={{ "--tone": RELATIONSHIP_TONE[character.relationship] } as CSSProperties}>
      <div className={styles.portrait} aria-hidden>
        {portrait ? <img src={portrait} alt="" /> : character.name.charAt(0)}
      </div>
      <div className={styles.body}>
        <h3 className={styles.name}>
          {onOpen ? (
            // Its ::after covers the card, so the whole card opens the detail view.
            <button type="button" className={styles.open} onClick={onOpen}>
              {character.name}
            </button>
          ) : (
            character.name
          )}
        </h3>
        {role && <p className={styles.role}>{role}</p>}
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
