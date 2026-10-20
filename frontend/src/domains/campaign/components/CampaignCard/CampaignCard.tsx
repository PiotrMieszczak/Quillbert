import { useCampaignImage } from "../../api/campaigns";
import type { Campaign } from "../../model/types";
import { CampaignBanner } from "../CampaignBanner";
import styles from "./CampaignCard.module.css";

type CampaignCardProps = {
  campaign: Campaign;
  onOpen: () => void;
};

export function CampaignCard({ campaign, onOpen }: CampaignCardProps) {
  const image = useCampaignImage(campaign.imageUrl);
  const played = campaign.sessionCount > 0 ? `Session ${campaign.sessionCount}` : "No sessions yet";
  return (
    <button type="button" className={styles.card} onClick={onOpen}>
      <CampaignBanner src={image.data ?? null} tint={campaign.tint} system={campaign.system} />
      <span className={styles.body}>
        <span className={styles.name}>{campaign.name}</span>
        <span className={styles.meta}>
          {played} · {campaign.system}
        </span>
      </span>
    </button>
  );
}
