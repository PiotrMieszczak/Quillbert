import { describe, expect, it } from "vitest";
import { emptyDraft } from "../model/types";
import { toBody, toCharacter, toDetail, type CharacterDto } from "./characters";

const dto: CharacterDto = {
  id: 4,
  name: "Brother Cael",
  isPlayer: false,
  relationship: "ally",
  role: null,
  level: null,
  location: null,
  tags: [],
  playerProfile: null,
};

describe("toCharacter", () => {
  it("gives an NPC no player and a string id", () => {
    expect(toCharacter(dto)).toMatchObject({ id: "4", role: "", player: null });
  });

  it("gives a player with an empty profile blank fields, not nulls", () => {
    const player = toCharacter({ ...dto, isPlayer: true, playerProfile: { playerName: null, class: "Cleric", race: null } });
    expect(player.player).toEqual({ playerName: "", class: "Cleric", race: "" });
  });
});

describe("toBody", () => {
  it("sends blank text as null and gives an NPC no profile", () => {
    const body = toBody({ ...emptyDraft(false), name: "  Ansel ", role: "  " });
    expect(body).toMatchObject({ name: "Ansel", role: null, isPlayer: false, stats: {} });
    expect("playerProfile" in body).toBe(false);
  });

  it("sends a player's profile, blanks as null", () => {
    const draft = emptyDraft(true);
    const body = toBody({ ...draft, name: "Cael", profile: { ...draft.profile, class: "Cleric" } });
    expect(body.playerProfile).toMatchObject({ class: "Cleric", playerName: null });
  });
});

describe("toDetail", () => {
  it("turns nulls into blanks the form can edit", () => {
    const detail = toDetail({ ...dto, disposition: null, lastSeen: null, quote: null, notes: null, bio: null, stats: {} });
    expect(detail).toMatchObject({ id: "4", role: "", notes: "", bio: "", profile: { playerName: "", bonds: "" } });
  });
});
