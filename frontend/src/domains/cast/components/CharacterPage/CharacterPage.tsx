import { useQueryClient } from "@tanstack/react-query";
import { useEffect, useState } from "react";
import {
  charactersKey,
  deleteCharacter,
  saveCharacter,
  uploadPortrait,
  useCharacter,
  usePortrait,
} from "../../api/characters";
import { useSheet } from "../../api/sheets";
import { emptyDraft, PORTRAIT_MAX_BYTES, PORTRAIT_TYPES, type CharacterDraft } from "../../model/types";
import { errorMessage, NumberRow, Panel, Prose, RecordMessage, RecordPage, Row } from "../RecordPage";
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

const DETAILS: ["location" | "disposition" | "lastSeen", string][] = [
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

/** One character, laid out like a sheet at the table: the stat block and story in the wide
 *  column, the facts beside it (docs/design/overview.md §4 → Detail views). The stat block
 *  follows the campaign system's sheet (ADR-0030). */
export function CharacterPage(props: CharacterPageProps) {
  const { campaignId, systemId, systemName, characterId, isPlayer, listLabel, onClose } = props;
  // Set once a new character exists, so a failed portrait upload can be retried without creating it twice.
  const [createdId, setCreatedId] = useState<string | null>(null);
  const id = characterId ?? createdId;
  const isNew = id === null;
  const queryClient = useQueryClient();
  const character = useCharacter(campaignId, id);
  const sheet = useSheet(systemId);
  // What was typed since the last save; null means the page shows what is saved.
  const [draft, setDraft] = useState<CharacterDraft | null>(isNew ? emptyDraft(isPlayer) : null);
  // Tags are typed as one comma-separated line and split on save.
  const [tags, setTags] = useState<string | null>(null);
  // A picked portrait waits for Save like every other change; `preview` is its blob URL.
  const [picked, setPicked] = useState<{ file: File; preview: string } | null>(null);
  const portrait = usePortrait(character.data?.portraitUrl ?? null).data ?? null;
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => () => void (picked && URL.revokeObjectURL(picked.preview)), [picked]);

  const shown = draft ?? character.data;
  if (!shown)
    return <RecordMessage listLabel={listLabel} onClose={onClose} error={character.error && errorMessage(character.error)} />;

  const set = <K extends keyof CharacterDraft>(key: K, value: CharacterDraft[K]) => setDraft({ ...shown, [key]: value });
  const text = (key: "role" | "quote" | "notes" | "bio" | (typeof DETAILS)[number][0]) => ({
    value: shown[key],
    onChange: (value: string) => set(key, value),
  });
  const profile = (key: keyof CharacterDraft["profile"]) => ({
    value: shown.profile[key],
    onChange: (value: string) => set("profile", { ...shown.profile, [key]: value }),
  });
  const kind = shown.isPlayer ? "player character" : "NPC";

  const pickPortrait = (file: File) => {
    if (!PORTRAIT_TYPES.includes(file.type)) return setError("The portrait must be a PNG, JPG or WebP image.");
    if (file.size > PORTRAIT_MAX_BYTES) return setError("The portrait must be 10 MB or smaller.");
    setError(null);
    setPicked({ file, preview: URL.createObjectURL(file) });
  };

  const discard = () => {
    setDraft(null);
    setTags(null);
    setPicked(null);
    setError(null);
  };

  const save = async () => {
    setBusy(true);
    setError(null);
    try {
      const body = { ...shown, tags: tags === null ? shown.tags : tags.split(",").map((tag) => tag.trim()).filter(Boolean) };
      // A change of portrait alone needs no write of the fields.
      let saved = isNew || draft || tags !== null ? await saveCharacter(campaignId, id, body, shown.stats === character.data?.stats) : character.data!;
      if (picked) {
        try {
          saved = await uploadPortrait(campaignId, saved.id, picked.file);
        } catch (failure) {
          // The fields are saved; say so, and let Save retry just the portrait on a saved character.
          await queryClient.invalidateQueries({ queryKey: charactersKey(campaignId) });
          queryClient.setQueryData([...charactersKey(campaignId), "one", saved.id], saved);
          setCreatedId(saved.id);
          setDraft(null);
          setTags(null);
          setError(`${isNew ? "The character was created" : "Your changes were saved"}, but the portrait did not upload. ${errorMessage(failure)}`);
          return;
        }
      }
      await queryClient.invalidateQueries({ queryKey: charactersKey(campaignId) });
      if (isNew) return onClose();
      queryClient.setQueryData([...charactersKey(campaignId), "one", id], saved);
      discard();
    } catch (failure) {
      setError(errorMessage(failure));
    } finally {
      setBusy(false);
    }
  };

  const remove = async () => {
    setBusy(true);
    try {
      await deleteCharacter(campaignId, id!);
      await queryClient.invalidateQueries({ queryKey: charactersKey(campaignId) });
      onClose();
    } catch (failure) {
      setError(errorMessage(failure));
      setBusy(false);
    }
  };

  return (
    <RecordPage
      listLabel={listLabel}
      name={shown.name}
      onName={(value) => set("name", value)}
      namePlaceholder={`Name this ${kind}`}
      subtitle={shown.role}
      onSubtitle={(value) => set("role", value)}
      subtitlePlaceholder="Role, e.g. Human Cleric"
      relationship={shown.relationship}
      onRelationship={(value) => set("relationship", value)}
      portrait={{ src: picked?.preview ?? portrait, accept: PORTRAIT_TYPES, onPick: pickPortrait }}
      isNew={isNew}
      dirty={draft !== null || tags !== null || picked !== null}
      busy={busy}
      canSave={shown.name.trim() !== ""}
      saveLabel={isNew ? `Create ${kind}` : "Save changes"}
      error={error}
      onClose={onClose}
      onSave={() => void save()}
      onDiscard={discard}
      onRemove={() => void remove()}
      side={
        <>
          <Panel title="Details">
            <NumberRow label="Level" value={shown.level} onChange={(value) => set("level", value)} min={0} max={99} />
            {DETAILS.map(([key, label]) => (
              <Row key={key} label={label} {...text(key)} />
            ))}
            <Row label="Tags" value={tags ?? shown.tags.join(", ")} onChange={setTags} maxLength={800} placeholder="Comma-separated" />
          </Panel>
          {shown.isPlayer && (
            <Panel title="Player">
              {PROFILE.map(([key, label]) => (
                <Row key={key} label={label} {...profile(key)} />
              ))}
              <Prose label="Bonds" {...profile("bonds")} />
            </Panel>
          )}
          <Panel title="GM notes" note="Private">
            <Prose label="Only you see these" {...text("notes")} maxLength={20000} placeholder="Secrets, plans, what not to reveal yet" />
          </Panel>
        </>
      }
    >
      <Panel title={sheet.data ? `${systemName} sheet` : "Stats"}>
        {sheet.data ? (
          <StatBlock sheet={sheet.data} stats={shown.stats} onChange={(stats) => set("stats", stats)} />
        ) : (
          <p className={styles.note}>
            {sheet.isError
              ? `Could not load the ${systemName} sheet. ${errorMessage(sheet.error)}`
              : sheet.data === null
                ? `No character sheet is saved for ${systemName} yet, so there is no stat block.`
                : "Loading the sheet…"}
          </p>
        )}
      </Panel>
      <Panel title="Story">
        <Prose label="Bio" {...text("bio")} maxLength={20000} placeholder="Where they come from and what they want" />
        <Prose label="Quote" {...text("quote")} placeholder="A line that sounds like them" />
      </Panel>
    </RecordPage>
  );
}
