import type { Campaign } from "../../../domains/campaign";
import styles from "./Header.module.css";

type HeaderProps = {
  campaign: Campaign;
  onSignOut: () => void;
};

export function Header({ campaign, onSignOut }: HeaderProps) {
  return (
    <header className={styles.header}>
      <div>
        <div className={styles.name}>{campaign.name}</div>
        <div className={styles.meta}>
          Session {campaign.sessionNumber} · {campaign.system}
        </div>
      </div>
      <div className={styles.actions}>
        <button type="button" className={styles.signOut} onClick={onSignOut}>
          Sign out
        </button>
        <button type="button" className={styles.avatar} aria-label="Settings">
          PM
        </button>
      </div>
    </header>
  );
}
