import type { Campaign } from "../../../domains/campaign";
import styles from "./Header.module.css";

type HeaderProps = {
  campaign: Campaign;
  onSignOut: () => void;
};

export function Header({ campaign, onSignOut }: HeaderProps) {
  return (
    <header className={styles.header}>
      {/* Session number and system return once a real campaign record supplies them. */}
      <div className={styles.name}>{campaign.name}</div>
      <div className={styles.actions}>
        <button type="button" className={styles.signOut} onClick={onSignOut}>
          Sign out
        </button>
      </div>
    </header>
  );
}
