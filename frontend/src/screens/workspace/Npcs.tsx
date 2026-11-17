import { useState } from "react";
import { type Campaign, useSystems } from "../../domains/campaign";
import { CardGrid, CharacterCard, CharacterPage, RelationshipFilter, useCharacters, type Relationship } from "../../domains/cast";
import { PageTitle } from "../../ui/components";
import styles from "./Cast.module.css";

export function Npcs({ campaign }: { campaign: Campaign }) {
  const [relationship, setRelationship] = useState<Relationship | null>(null);
  // The character shown in place of the list; id null is a new one.
  const [open, setOpen] = useState<{ id: string | null } | null>(null);
  const npcs = useCharacters(campaign.id, { isPlayer: false, relationship });
  // The campaign carries its system's name, not the id the sheet is keyed by.
  const systemId = useSystems().data?.find((system) => system.name === campaign.system)?.id;
  if (open)
    return (
      <CharacterPage
        campaignId={campaign.id}
        systemId={systemId}
        systemName={campaign.system}
        characterId={open.id}
        isPlayer={false}
        listLabel="NPCs"
        onClose={() => setOpen(null)}
      />
    );
  return (
    <div className={styles.view}>
      <header className={styles.header}>
        <div className={styles.heading}>
          <PageTitle>NPCs</PageTitle>
          <p className={styles.sub}>The cast the party has met, by how they stand toward it.</p>
        </div>
        <button type="button" className={styles.add} onClick={() => setOpen({ id: null })}>
          Add NPC
        </button>
      </header>
      <RelationshipFilter value={relationship} onChange={setRelationship} />
      <CardGrid query={npcs} empty={relationship ? "No NPCs with this relationship yet." : "No NPCs in this campaign yet."}>
        {(character) => <CharacterCard character={character} onOpen={() => setOpen({ id: character.id })} />}
      </CardGrid>
    </div>
  );
}
