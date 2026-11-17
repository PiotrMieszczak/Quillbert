// @vitest-environment jsdom
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import type { Sheet, Stats } from "../../model/types";
import { StatBlock } from "./StatBlock";

afterEach(cleanup);

const SHEET: Sheet = {
  sections: [
    {
      key: "characteristics",
      label: "Characteristics",
      fields: [{ key: "STR", label: "Strength", type: "int", min: 0, max: 15 }],
    },
    {
      key: "skills",
      label: "Skills",
      fields: [
        {
          key: "skills",
          label: "Skill",
          type: "list",
          itemFields: [
            { key: "name", label: "Name", type: "text" },
            { key: "level", label: "Level", type: "int", min: 0, max: 4 },
          ],
        },
      ],
    },
  ],
};

describe("StatBlock", () => {
  it("shows values by section and field, leaving the unset ones empty", () => {
    render(<StatBlock sheet={SHEET} stats={{ skills: { skills: [{ name: "Pilot", level: 2 }] } }} onChange={() => {}} />);

    expect((screen.getByLabelText("Strength") as HTMLInputElement).value).toBe("");
    expect(screen.getByDisplayValue("Pilot")).toBeTruthy();
    expect((screen.getByLabelText("Level") as HTMLInputElement).value).toBe("2");
  });

  it("shows stats saved before the sheet as empty instead of breaking", () => {
    const legacy = { characteristics: 7, skills: { skills: "Pilot 1" } } as unknown as Stats;
    render(<StatBlock sheet={SHEET} stats={legacy} onChange={() => {}} />);

    expect((screen.getByLabelText("Strength") as HTMLInputElement).value).toBe("");
    expect(screen.queryByRole("table")).toBeNull();
  });

  it("writes a number under its section and drops a cleared field", () => {
    const onChange = vi.fn();
    render(<StatBlock sheet={SHEET} stats={{ characteristics: { STR: 7 } }} onChange={onChange} />);

    fireEvent.change(screen.getByLabelText("Strength"), { target: { value: "9" } });
    expect(onChange).toHaveBeenLastCalledWith({ characteristics: { STR: 9 } });
    fireEvent.change(screen.getByLabelText("Strength"), { target: { value: "" } });
    expect(onChange).toHaveBeenLastCalledWith({ characteristics: {} });
  });

  it("adds and removes rows of a list field", () => {
    const onChange = vi.fn();
    const stats = { skills: { skills: [{ name: "Pilot" }] } };
    render(<StatBlock sheet={SHEET} stats={stats} onChange={onChange} />);

    fireEvent.click(screen.getByRole("button", { name: "Add skill" }));
    expect(onChange).toHaveBeenLastCalledWith({ skills: { skills: [{ name: "Pilot" }, {}] } });
    fireEvent.click(screen.getByRole("button", { name: "Remove Skill row 1" }));
    expect(onChange).toHaveBeenLastCalledWith({ skills: {} });
  });
});
