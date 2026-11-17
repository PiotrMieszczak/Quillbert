import { useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { deleteFaction, factionsKey, saveFaction, useFactions } from "../../api/factions";
import { emptyFaction, type FactionDraft } from "../../model/types";
import { errorMessage, Field, RecordMessage, RecordPage, RelationshipField, Section } from "../RecordPage";

type FactionPageProps = {
  campaignId: string;
  /** null creates a new faction. */
  factionId: string | null;
  onClose: () => void;
};

const SHORT: ["type" | "influence" | "reach", string][] = [
  ["type", "Type"],
  ["influence", "Influence"],
  ["reach", "Reach"],
];

/** One faction: read, edited or created in the same layout as a character
 *  (docs/design/overview.md §4 → Detail views). */
export function FactionPage({ campaignId, factionId, onClose }: FactionPageProps) {
  const queryClient = useQueryClient();
  const factions = useFactions(campaignId);
  // The draft exists only while editing; a new faction starts in it.
  const [draft, setDraft] = useState<FactionDraft | null>(factionId === null ? emptyFaction() : null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const saved = factions.data?.find((faction) => faction.id === factionId);
  const shown = draft ?? saved;
  if (!shown)
    return (
      <RecordMessage
        listLabel="Factions"
        onClose={onClose}
        // Loaded but absent: it was deleted elsewhere.
        error={factions.error ?? (factions.data ? new Error("gone") : null)}
      />
    );

  const editing = draft !== null;
  const text = (key: keyof FactionDraft & string) => ({
    value: shown[key],
    onChange: editing ? (value: string) => setDraft((current) => current && { ...current, [key]: value }) : undefined,
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
      title={shown.name || "New faction"}
      relationship={shown.relationship}
      editing={editing}
      busy={busy}
      canSave={shown.name.trim() !== ""}
      saveLabel={factionId === null ? "Create faction" : "Save changes"}
      error={error}
      onClose={onClose}
      onSave={() =>
        draft && void run(() => saveFaction(campaignId, factionId, draft), () => (factionId === null ? onClose() : setDraft(null)))
      }
      onCancel={() => (factionId === null ? onClose() : (setDraft(null), setError(null)))}
      onEdit={() => setDraft(shown)}
      onRemove={() => void run(() => deleteFaction(campaignId, factionId!), onClose)}
    >
      <Section label="Details" grid>
        {editing && <Field label="Name" {...text("name")} required />}
        {editing && (
          <RelationshipField
            value={shown.relationship}
            onChange={(relationship) => setDraft((current) => current && { ...current, relationship })}
          />
        )}
        {SHORT.map(([key, label]) => (
          <Field key={key} label={label} {...text(key)} />
        ))}
      </Section>
      <Section label="Purpose">
        <Field label="Motto" {...text("motto")} maxLength={2000} long />
        <Field label="Goal" {...text("goal")} maxLength={2000} long />
      </Section>
      <Section label="Notes">
        <Field label="GM notes (private)" {...text("notes")} maxLength={20000} long />
      </Section>
    </RecordPage>
  );
}
