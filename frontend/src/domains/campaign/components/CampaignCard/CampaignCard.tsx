import type { PointerEvent } from "react";
import { useCampaignImage } from "../../api/campaigns";
import type { Campaign } from "../../model/types";
import { CampaignBanner } from "../CampaignBanner";
import styles from "./CampaignCard.module.css";

type CampaignCardProps = {
  campaign: Campaign;
  onOpen: () => void;
};

/** Tilt toward the mouse, with a sheen at the cursor. Touch and pen get the plain card. */
function tilt(event: PointerEvent<HTMLElement>) {
  if (event.pointerType !== "mouse") return;
  const el = event.currentTarget, r = el.getBoundingClientRect();
  const px = (event.clientX - r.left) / r.width, py = (event.clientY - r.top) / r.height;
  el.style.setProperty("--rx", `${(0.5 - py) * 7}deg`);
  el.style.setProperty("--ry", `${(px - 0.5) * 9}deg`);
  el.style.setProperty("--mx", `${px * 100}%`);
  el.style.setProperty("--my", `${py * 100}%`);
  el.style.setProperty("--lift", "-4px");
  el.style.setProperty("--sheen", "1");
}

function untilt(event: PointerEvent<HTMLElement>) {
  for (const name of ["--rx", "--ry", "--lift", "--sheen"]) event.currentTarget.style.removeProperty(name);
}

export function CampaignCard({ campaign, onOpen }: CampaignCardProps) {
  const image = useCampaignImage(campaign.imageUrl);
  const played = campaign.sessionCount > 0 ? `Session ${campaign.sessionCount}` : "No sessions yet";
  return (
    <button type="button" className={styles.card} onClick={onOpen} onPointerMove={tilt} onPointerLeave={untilt}>
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
