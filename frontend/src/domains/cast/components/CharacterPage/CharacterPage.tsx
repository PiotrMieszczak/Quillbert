import { useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { Badge } from "../../../../ui/components";
import { charactersKey, deleteCharacter, saveCharacter, useCharacter } from "../../api/characters";
import { useSheet } from "../../api/sheets";
import { emptyDraft, type CharacterDraft } from "../../model/types";
import { errorMessage, Field, NumberField, RecordMessage, RecordPage, RelationshipField, Section } from "../RecordPage";
import { StatBlock } from "../StatBlock";
import styles from "./CharacterPage.module.css";

type CharacterPageProps = {
  campaignId: string;
  /** The campaign's system; undefined while the systems list loads. */
  systemId: string | undefined;
  systemName: string;
  /** null creates a new character of the kind `isPlayer` says. */
  characterId: string | null;
  isPlayer: boolean;
  /** The list this page was opened from, for the back link. */
  listLabel: string;
  onClose: () => void;
};

const TEXT: ["role" | "location" | "disposition" | "lastSeen", string][] = [
  ["role", "Role"],
  ["location", "Location"],
  ["disposition", "Disposition"],
  ["lastSeen", "Last seen"],
];

const PROFILE: [keyof CharacterDraft["profile"], string][] = [
  ["playerName", "Player"],
  ["class", "Class"],
  ["race", "Race"],
  ["background", "Background"],
  ["xp", "XP"],
  ["pronouns", "Pronouns"],
];

/** One character: read, edited or created in the same layout (docs/design/overview.md §4 →
 *  Detail views). The stat block follows the campaign system's sheet (ADR-0030). */
export function CharacterPage(props: CharacterPageProps) {
  const { campaignId, systemId, systemName, characterId, isPlayer, listLabel, onClose } = props;
  const queryClient = useQueryClient();
  const character = useCharacter(campaignId, characterId);
  const sheet = useSheet(systemId);
  // The draft exists only while editing; a new character starts in it.
  const [draft, setDraft] = useState<CharacterDraft | null>(characterId === null ? emptyDraft(isPlayer) : null);
  const [tags, setTags] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const shown = draft ?? character.data;
  if (!shown) return <RecordMessage listLabel={listLabel} onClose={onClose} error={character.error} />;

  const editing = draft !== null;
  const set = <K extends keyof CharacterDraft>(key: K, value: CharacterDraft[K]) =>
    setDraft((current) => current && { ...current, [key]: value });
  const kind = shown.isPlayer ? "player character" : "NPC";

  const save = async () => {
    if (!draft) return;
    setBusy(true);
    setError(null);
    try {
      const body = { ...draft, tags: tags.split(",").map((tag) => tag.trim()).filter(Boolean) };
      const saved = await saveCharacter(campaignId, characterId, body, draft.stats === character.data?.stats);
      await queryClient.invalidateQueries({ queryKey: charactersKey(campaignId) });
      if (characterId === null) return onClose();
      queryClient.setQueryData([...charactersKey(campaignId), "one", characterId], saved);
      setDraft(null);
    } catch (failure) {
      setError(errorMessage(failure));
    } finally {
      setBusy(false);
    }
  };

  const remove = async () => {
    setBusy(true);
    try {
      await deleteCharacter(campaignId, characterId!);
      await queryClient.invalidateQueries({ queryKey: charactersKey(campaignId) });
      onClose();
    } catch (failure) {
      setError(errorMessage(failure));
      setBusy(false);
    }
  };

  const text = (key: "quote" | "notes" | "bio" | (typeof TEXT)[number][0]) =>
    ({ value: shown[key], onChange: editing ? (value: string) => set(key, value) : undefined });
  const profile = (key: keyof CharacterDraft["profile"]) => ({
    value: shown.profile[key],
    onChange: editing ? (value: string) => set("profile", { ...shown.profile, [key]: value }) : undefined,
  });

  return (
    <RecordPage
      listLabel={listLabel}
      title={shown.name || `New ${kind}`}
      relationship={shown.relationship}
      editing={editing}
      busy={busy}
      canSave={shown.name.trim() !== ""}
      saveLabel={characterId === null ? `Create ${kind}` : "Save changes"}
      error={error}
      onClose={onClose}
      onSave={() => void save()}
      onCancel={() => (characterId === null ? onClose() : (setDraft(null), setError(null)))}
      onEdit={() => {
        setTags(shown.tags.join(", "));
        setError(null);
        setDraft(shown);
      }}
      onRemove={() => void remove()}
    >
      <Section label="Details" grid>
        {editing && <Field label="Name" value={shown.name} onChange={(value) => set("name", value)} required />}
        {editing && <RelationshipField value={shown.relationship} onChange={(value) => set("relationship", value)} />}
        {TEXT.map(([key, label]) => (
          <Field key={key} label={label} {...text(key)} />
        ))}
        {editing ? (
          <NumberField label="Level" value={shown.level} onChange={(value) => set("level", value)} min={0} max={99} />
        ) : (
          <Field label="Level" value={shown.level?.toString()} />
        )}
        {editing ? (
          <Field label="Tags, separated by commas" value={tags} onChange={setTags} maxLength={800} />
        ) : (
          <Field label="Tags">
            <span className={styles.tags}>
              {shown.tags.length > 0 ? shown.tags.map((tag) => <Badge key={tag}>{tag}</Badge>) : "—"}
            </span>
          </Field>
        )}
      </Section>

      {shown.isPlayer && (
        <Section label="Player" title grid footer={<Field label="Bonds" {...profile("bonds")} maxLength={2000} long />}>
          {PROFILE.map(([key, label]) => (
            <Field key={key} label={label} {...profile(key)} />
          ))}
        </Section>
      )}

      <Section label="Stats" title>
        {sheet.data ? (
          <StatBlock sheet={sheet.data} stats={shown.stats} onChange={editing ? (stats) => set("stats", stats) : undefined} />
        ) : (
          <p className={styles.note}>
            {sheet.isError
              ? `Could not load the ${systemName} sheet. ${errorMessage(sheet.error)}`
              : sheet.data === null
                ? `No character sheet is saved for ${systemName} yet, so there is no stat block.`
                : "Loading the sheet…"}
          </p>
        )}
      </Section>

      <Section label="Story and notes">
        <Field label="Bio" {...text("bio")} maxLength={20000} long />
        <Field label="Quote" {...text("quote")} maxLength={2000} long />
        <Field label="GM notes (private)" {...text("notes")} maxLength={20000} long />
      </Section>
    </RecordPage>
  );
}
