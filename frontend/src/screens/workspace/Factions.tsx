import { useState } from "react";
import type { Campaign } from "../../domains/campaign";
import { CardGrid, FactionCard, FactionPage, useFactions } from "../../domains/cast";
import { PageTitle } from "../../ui/components";
import styles from "./Cast.module.css";

export function Factions({ campaign }: { campaign: Campaign }) {
  // The faction shown in place of the list; id null is a new one.
  const [open, setOpen] = useState<{ id: string | null } | null>(null);
  const factions = useFactions(campaign.id);
  if (open) return <FactionPage campaignId={campaign.id} factionId={open.id} onClose={() => setOpen(null)} />;
  return (
    <div className={styles.view}>
      <header className={styles.header}>
        <div className={styles.heading}>
          <PageTitle>Factions</PageTitle>
          <p className={styles.sub}>The powers in play and where the party stands with each.</p>
        </div>
        <button type="button" className={styles.add} onClick={() => setOpen({ id: null })}>
          Add faction
        </button>
      </header>
      <CardGrid query={factions} empty="No factions in this campaign yet.">
        {(faction) => <FactionCard faction={faction} onOpen={() => setOpen({ id: faction.id })} />}
      </CardGrid>
    </div>
  );
}
