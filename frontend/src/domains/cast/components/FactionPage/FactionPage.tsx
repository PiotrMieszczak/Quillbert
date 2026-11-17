import { useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { deleteFaction, factionsKey, saveFaction, useFactions } from "../../api/factions";
import { emptyFaction, type FactionDraft } from "../../model/types";
import { errorMessage, Panel, Prose, RecordMessage, RecordPage, Row } from "../RecordPage";

type FactionPageProps = {
  campaignId: string;
  /** null creates a new faction. */
  factionId: string | null;
  onClose: () => void;
};

/** One faction, in the same frame as a character (docs/design/overview.md §4 → Detail views). */
export function FactionPage({ campaignId, factionId, onClose }: FactionPageProps) {
  const isNew = factionId === null;
  const queryClient = useQueryClient();
  const factions = useFactions(campaignId);
  // What was typed since the last save; null means the page shows what is saved.
  const [draft, setDraft] = useState<FactionDraft | null>(isNew ? emptyFaction() : null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const saved = factions.data?.find((faction) => faction.id === factionId);
  const shown = draft ?? saved;
  if (!shown) {
    // Loaded but absent: it was deleted elsewhere.
    const problem = factions.error ? errorMessage(factions.error) : factions.data ? "This faction no longer exists." : null;
    return <RecordMessage listLabel="Factions" onClose={onClose} error={problem} />;
  }

  const set = <K extends keyof FactionDraft>(key: K, value: FactionDraft[K]) => setDraft({ ...shown, [key]: value });
  const text = (key: Exclude<keyof FactionDraft, "relationship">) => ({
    value: shown[key],
    onChange: (value: string) => set(key, value),
  });

  const run = async (action: () => Promise<unknown>, done: () => void) => {
    setBusy(true);
    setError(null);
    try {
      await action();
      await queryClient.invalidateQueries({ queryKey: factionsKey(campaignId) });
      done();
    } catch (failure) {
      setError(errorMessage(failure));
    } finally {
      setBusy(false);
    }
  };

  return (
    <RecordPage
      listLabel="Factions"
      name={shown.name}
      onName={(value) => set("name", value)}
      namePlaceholder="Name this faction"
      subtitle={shown.type}
      onSubtitle={(value) => set("type", value)}
      subtitlePlaceholder="Type, e.g. Merchant guild"
      relationship={shown.relationship}
      onRelationship={(value) => set("relationship", value)}
      isNew={isNew}
      dirty={draft !== null}
      busy={busy}
      canSave={shown.name.trim() !== ""}
      saveLabel={isNew ? "Create faction" : "Save changes"}
      error={error}
      onClose={onClose}
      onSave={() => void run(() => saveFaction(campaignId, factionId, shown), () => (isNew ? onClose() : setDraft(null)))}
      onDiscard={() => {
        setDraft(null);
        setError(null);
      }}
      onRemove={() => void run(() => deleteFaction(campaignId, factionId!), onClose)}
      side={
        <>
          <Panel title="Details">
            <Row label="Influence" {...text("influence")} placeholder="High, Unknown…" />
            <Row label="Reach" {...text("reach")} placeholder="Old Quarter, Everywhere…" />
          </Panel>
          <Panel title="GM notes" note="Private">
            <Prose label="Only you see these" {...text("notes")} maxLength={20000} placeholder="Secrets, plans, what not to reveal yet" />
          </Panel>
        </>
      }
    >
      <Panel title="Purpose">
        <Prose label="Motto" {...text("motto")} placeholder="What they say about themselves" />
        <Prose label="Goal" {...text("goal")} placeholder="What they are working toward" />
      </Panel>
    </RecordPage>
  );
}
