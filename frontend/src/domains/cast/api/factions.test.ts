import { describe, expect, it } from "vitest";
import { emptyFaction } from "../model/types";
import { toFaction, toFactionBody } from "./factions";

describe("faction mapping", () => {
  it("turns the wire's nulls into blanks the form can edit", () => {
    const faction = toFaction({
      id: 2,
      name: "The Pale Court",
      relationship: "enemy",
      type: "Hidden cabal",
      influence: null,
      reach: null,
      motto: null,
      goal: null,
      notes: null,
    });
    expect(faction).toMatchObject({ id: "2", type: "Hidden cabal", influence: "", notes: "" });
  });

  it("sends blank text as null and trims the name", () => {
    expect(toFactionBody({ ...emptyFaction(), name: " The Pale Court ", motto: "  ", goal: "Rule" })).toEqual({
      name: "The Pale Court",
      relationship: "neutral",
      type: null,
      influence: null,
      reach: null,
      motto: null,
      goal: "Rule",
      notes: null,
    });
  });
});
