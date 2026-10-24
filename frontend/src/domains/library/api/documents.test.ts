import { describe, expect, it } from "vitest";
import { documentsKey } from "./documents";

describe("documentsKey", () => {
  it("separates a campaign's list from the GM library", () => {
    expect(documentsKey({ campaignId: "ashfall" })).toEqual(["documents", "ashfall"]);
    expect(documentsKey("library")).toEqual(["documents", "library"]);
  });

  // The library key has no user id: App clears the query cache on sign-out instead.
  it("is the same for every GM, which is why sign-out must clear the cache", () => {
    expect(documentsKey("library")).toEqual(documentsKey("library"));
  });
});
