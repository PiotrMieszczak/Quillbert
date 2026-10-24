import { describe, expect, it } from "vitest";
import { type CitationDto, toCitation } from "./conversations";

const dto: CitationDto = {
  label: "S1",
  chunkId: 812,
  documentId: 1,
  filename: "Core Rulebook v3.pdf",
  pageFrom: 195,
  heading: "Opportunity Attacks",
  attribution: null,
};

describe("toCitation", () => {
  it("keeps the document id as a string, so the chip can open Documents", () => {
    expect(toCitation(dto)).toEqual({
      label: "S1",
      documentId: "1",
      filename: "Core Rulebook v3.pdf",
      page: 195,
      heading: "Opportunity Attacks",
      attribution: null,
    });
  });

  it("carries a library passage's layer (ADR-0027)", () => {
    expect(toCitation({ ...dto, attribution: "My library" }).attribution).toBe("My library");
  });
});
