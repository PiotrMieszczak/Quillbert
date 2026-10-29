import { useQueryClient } from "@tanstack/react-query";
import { useEffect, useId, useRef, useState, type ChangeEvent, type FormEvent } from "react";
import { ApiError } from "../../../../lib/api";
import { campaignsKey, createCampaign, uploadCampaignImage, useSystems } from "../../api/campaigns";
import { BANNER_MAX_BYTES, BANNER_TYPES, editionFor, tintFor } from "../../model/systems";
import type { Campaign } from "../../model/types";
import { CampaignBanner } from "../CampaignBanner";
import styles from "./AddCampaignModal.module.css";

type AddCampaignModalProps = {
  onClose: () => void;
  /** The campaign exists (and has its banner, when one was chosen). */
  onCreated: (campaign: Campaign) => void;
};

const message = (error: unknown) => (error instanceof ApiError ? error.message : "Check your connection and try again.");

/** Name, banner and a mandatory system (docs/design/overview.md §2). Create stays disabled until
 *  both a name and a system are set. */
export function AddCampaignModal({ onClose, onCreated }: AddCampaignModalProps) {
  const dialog = useRef<HTMLDialogElement>(null);
  const nameRef = useRef<HTMLInputElement>(null);
  const titleId = useId();
  const fileId = useId();
  const queryClient = useQueryClient();
  const systems = useSystems();
  const [name, setName] = useState("");
  const [systemId, setSystemId] = useState<string | null>(null);
  const [banner, setBanner] = useState<{ file: File; preview: string } | null>(null);
  const previewUrl = useRef<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  // Set once the campaign exists, so a failed banner upload is retried without a second campaign.
  const [created, setCreated] = useState<Campaign | null>(null);

  useEffect(() => {
    dialog.current?.showModal();
    // showModal() focuses the first focusable element (the × button) and overrides autoFocus.
    nameRef.current?.focus();
  }, []);

  const chooseBanner = (file: File | null) => {
    if (previewUrl.current) URL.revokeObjectURL(previewUrl.current);
    previewUrl.current = file && URL.createObjectURL(file);
    setBanner(file && { file, preview: previewUrl.current! });
  };

  useEffect(
    () => () => {
      if (previewUrl.current) URL.revokeObjectURL(previewUrl.current);
    },
    [],
  );

  const close = () => {
    if (created) void queryClient.invalidateQueries({ queryKey: campaignsKey });
    onClose();
  };

  const pickImage = (event: ChangeEvent<HTMLInputElement>) => {
    const picked = event.target.files?.[0];
    event.target.value = ""; // picking the same file again still fires change
    if (!picked) return;
    if (!BANNER_TYPES.includes(picked.type)) return setError("The banner must be a PNG, JPG or WebP image.");
    if (picked.size > BANNER_MAX_BYTES) return setError("The banner must be 10 MB or smaller.");
    setError(null);
    chooseBanner(picked);
  };

  const trimmed = name.trim();
  const system = systems.data?.find((s) => s.id === systemId) ?? null;
  const ready = trimmed !== "" && system !== null && !busy;

  const submit = async (event: FormEvent) => {
    event.preventDefault();
    if (!ready) return;
    setBusy(true);
    setError(null);
    let campaign = created;
    try {
      campaign ??= await createCampaign({ name: trimmed, systemId: system.id, tint: tintFor(system.id) });
      setCreated(campaign);
      if (banner) campaign = await uploadCampaignImage(campaign.id, banner.file);
      await queryClient.invalidateQueries({ queryKey: campaignsKey });
      onCreated(campaign);
    } catch (failure) {
      setError(
        campaign
          ? `“${campaign.name}” was created, but its banner did not upload. ${message(failure)}`
          : message(failure),
      );
      setBusy(false);
    }
  };

  const action = busy ? "Creating…" : created ? (banner ? "Retry upload" : "Open campaign") : "Create campaign";

  return (
    <dialog
      ref={dialog}
      className={styles.dialog}
      aria-labelledby={titleId}
      onCancel={(event) => {
        event.preventDefault();
        close();
      }}
    >
      <form className={styles.form} onSubmit={submit}>
        <div className={styles.head}>
          <h2 id={titleId} className={styles.title}>
            New Campaign
          </h2>
          <button type="button" className={styles.close} onClick={close} aria-label="Close">
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="1.7">
              <path d="M3.5 3.5l7 7M10.5 3.5l-7 7" strokeLinecap="round" />
            </svg>
          </button>
        </div>

        <div className={styles.upload}>
          {/* One file input for both states; the drop zone and the Change chip are its labels. */}
          <input
            id={fileId}
            className={styles.fileInput}
            type="file"
            accept={BANNER_TYPES.join(",")}
            onChange={pickImage}
            disabled={busy}
            aria-label="Banner image"
          />
          {banner ? (
            <div className={styles.filled}>
              <CampaignBanner
                className={styles.preview}
                src={banner.preview}
                tint={system ? tintFor(system.id) : "var(--accent)"}
                system={system?.name ?? null}
              >
                <span className={styles.previewName}>{trimmed || "Untitled campaign"}</span>
              </CampaignBanner>
              <div className={styles.tools}>
                <label htmlFor={fileId} className={[styles.chip, styles.change].join(" ")}>
                  Change
                </label>
                <button type="button" className={styles.chip} onClick={() => chooseBanner(null)} disabled={busy}>
                  Remove
                </button>
              </div>
            </div>
          ) : (
            <label htmlFor={fileId} className={styles.drop}>
              <span className={styles.icon} aria-hidden>
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6">
                  <path
                    d="M12 16V4m0 0L8 8m4-4l4 4M4 16v2a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  />
                </svg>
              </span>
              <span className={styles.emptyTitle}>Add a banner image</span>
              <span className={styles.hint}>PNG, JPG or WebP · optional · the card uses a tint until you add one</span>
            </label>
          )}
        </div>

        <label className={styles.field}>
          <span className={styles.label}>
            Campaign name <span className={styles.required}>*</span>
          </span>
          <input
            className={styles.input}
            value={name}
            onChange={(event) => setName(event.target.value)}
            placeholder="e.g. Ashfall Reach"
            maxLength={120}
            ref={nameRef}
            disabled={busy || created !== null}
          />
        </label>

        <fieldset className={styles.systems} disabled={busy || created !== null}>
          <legend className={styles.label}>
            Game system <span className={styles.required}>*</span>
          </legend>
          {systems.isError && <p className={styles.error}>Could not load the game systems. {message(systems.error)}</p>}
          <div className={styles.systemGrid} role="radiogroup" aria-label="Game system">
            {systems.data?.map((option) => (
              <button
                key={option.id}
                type="button"
                role="radio"
                aria-checked={option.id === systemId}
                className={styles.system}
                onClick={() => setSystemId(option.id)}
              >
                <span className={styles.systemName}>{option.name}</span>
                <span className={styles.edition}>{editionFor(option.id)}</span>
              </button>
            ))}
          </div>
        </fieldset>

        {error && (
          <p className={styles.error} role="alert">
            {error}
          </p>
        )}

        <div className={styles.actions}>
          <button type="button" className={styles.cancel} onClick={close}>
            Cancel
          </button>
          <button type="submit" className={styles.create} disabled={!ready}>
            {action}
          </button>
        </div>
      </form>
    </dialog>
  );
}
