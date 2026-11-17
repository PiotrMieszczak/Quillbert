import { useState } from "react";
import { type Campaign, useSystems } from "../../domains/campaign";
import { CardGrid, CharacterCard, CharacterPage, useCharacters } from "../../domains/cast";
import { PageTitle } from "../../ui/components";
import styles from "./Cast.module.css";

export function Players({ campaign }: { campaign: Campaign }) {
  // The character shown in place of the list; id null is a new one.
  const [open, setOpen] = useState<{ id: string | null } | null>(null);
  const players = useCharacters(campaign.id, { isPlayer: true });
  // The campaign carries its system's name, not the id the sheet is keyed by.
  const systemId = useSystems().data?.find((system) => system.name === campaign.system)?.id;
  if (open)
    return (
      <CharacterPage
        campaignId={campaign.id}
        systemId={systemId}
        systemName={campaign.system}
        characterId={open.id}
        isPlayer
        listLabel="Party"
        onClose={() => setOpen(null)}
      />
    );
  return (
    <div className={styles.view}>
      <header className={styles.header}>
        <div className={styles.heading}>
          <PageTitle>Party</PageTitle>
          <p className={styles.sub}>The player characters and who plays them.</p>
        </div>
        <button type="button" className={styles.add} onClick={() => setOpen({ id: null })}>
          Add Player
        </button>
      </header>
      <CardGrid query={players} empty="No player characters in this campaign yet.">
        {(character) => <CharacterCard character={character} onOpen={() => setOpen({ id: character.id })} />}
      </CardGrid>
    </div>
  );
}
