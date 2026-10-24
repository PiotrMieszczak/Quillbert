import { describe, expect, it } from "vitest";
import { pendingFromFile } from "./queued";

describe("pendingFromFile", () => {
  const file = new File(["%PDF"], "Core.pdf");

  it("is an Uploading row with no tags while the request is in flight", () => {
    expect(pendingFromFile(file, "p1")).toMatchObject({
      id: "p1",
      name: "Core.pdf",
      kind: "PDF",
      status: "Uploading",
      systems: [],
    });
  });

  it("is a Failed row with the server's reason when refused", () => {
    expect(pendingFromFile(file, "p1", "File too large")).toMatchObject({
      status: "Failed",
      meta: "File too large",
    });
  });
});
