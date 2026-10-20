import type { CSSProperties, ReactNode } from "react";
import styles from "./CampaignBanner.module.css";

type CampaignBannerProps = {
  /** An image URL the browser can load (a blob or object URL), or null for the tint gradient. */
  src: string | null;
  tint: string;
  /** Shown as the badge in the top-left corner; omitted when null. */
  system: string | null;
  className?: string;
  children?: ReactNode;
};

/** The banner of a campaign card. The add-campaign modal reuses it as the live preview. */
export function CampaignBanner({ src, tint, system, className, children }: CampaignBannerProps) {
  return (
    <span
      className={[styles.banner, className].filter(Boolean).join(" ")}
      style={{ "--tint": tint } as CSSProperties}
    >
      {src && <img className={styles.image} src={src} alt="" />}
      <span className={styles.shade} aria-hidden />
      {system && <span className={styles.badge}>{system}</span>}
      {children}
    </span>
  );
}
