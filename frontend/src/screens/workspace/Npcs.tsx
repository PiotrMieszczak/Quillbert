import { useState } from "react";
import { CharacterCard, NPCS, RelationshipFilter, type Relationship } from "../../domains/cast";
import { Badge, PageTitle } from "../../ui/components";
import styles from "./Cast.module.css";

export function Npcs() {
  const [relationship, setRelationship] = useState<Relationship | null>(null);
  const shown = relationship ? NPCS.filter((npc) => npc.relationship === relationship) : NPCS;
  return (
    <div className={styles.view}>
      <header className={styles.header}>
        <div className={styles.heading}>
          <PageTitle>NPCs</PageTitle>
          <p className={styles.sub}>The cast the party has met, by how they stand toward it.</p>
        </div>
        <Badge>Sample data</Badge>
      </header>
      <RelationshipFilter value={relationship} onChange={setRelationship} />
      {shown.length > 0 ? (
        <ul className={styles.grid}>
          {shown.map((npc) => (
            <li key={npc.id}>
              <CharacterCard character={npc} />
            </li>
          ))}
        </ul>
      ) : (
        <p className={styles.empty}>No NPCs with this relationship yet.</p>
      )}
    </div>
  );
}
