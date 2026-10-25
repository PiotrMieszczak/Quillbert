// @vitest-environment jsdom
import { cleanup, render, screen, within } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { ACTIVITY } from "../../model/fixtures";
import { ActivityList } from "./ActivityList";

afterEach(cleanup);

describe("ActivityList", () => {
  it("renders one row per entry with its kind label", () => {
    render(<ActivityList entries={ACTIVITY} />);

    const rows = screen.getAllByRole("listitem");
    expect(rows).toHaveLength(ACTIVITY.length);
    expect(within(rows[0]).getByText("Session")).toBeTruthy();
    expect(within(rows[1]).getByText("NPC")).toBeTruthy();
    expect(within(rows[0]).getByText(ACTIVITY[0].title)).toBeTruthy();
  });
});
