import type { Campaign } from "../../../domains/campaign";
import styles from "./Header.module.css";

type HeaderProps = {
  campaign: Campaign;
  onSwitchCampaign: () => void;
  onSignOut: () => void;
};

export function Header({ campaign, onSwitchCampaign, onSignOut }: HeaderProps) {
  return (
    <header className={styles.header}>
      <button type="button" className={styles.campaign} onClick={onSwitchCampaign} title="Switch campaign">
        <span className={styles.name}>{campaign.name}</span>
        <span className={styles.system}>{campaign.system}</span>
      </button>
      <div className={styles.actions}>
        <button type="button" className={styles.signOut} onClick={onSignOut}>
          Sign out
        </button>
      </div>
    </header>
  );
}
