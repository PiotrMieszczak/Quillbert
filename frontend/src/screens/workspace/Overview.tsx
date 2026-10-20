import { ACTIVITY, ActivityList, CAMPAIGN, STATS, StatGrid } from "../../domains/campaign";
import { Card, Eyebrow, PageTitle, SectionTitle } from "../../ui/components";
import styles from "./Overview.module.css";

export function Overview() {
  return (
    <div className={styles.view}>
      <Card className={styles.hero}>
        <Eyebrow>Campaign</Eyebrow>
        <PageTitle>{CAMPAIGN.name}</PageTitle>
        <p className={styles.lede}>
          Session {CAMPAIGN.sessionCount} of an ongoing {CAMPAIGN.system} campaign. Your
          material is indexed and searchable; the cast, factions, and quest log below track
          what the party has touched so far.
        </p>
      </Card>

      <section className={styles.section}>
        <SectionTitle>At a glance</SectionTitle>
        <StatGrid stats={STATS} />
      </section>

      <section className={styles.section}>
        <SectionTitle>Recent activity</SectionTitle>
        <ActivityList entries={ACTIVITY} />
      </section>
    </div>
  );
}
