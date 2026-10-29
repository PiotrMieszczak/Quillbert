// @vitest-environment jsdom
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import type { Message } from "../../model/types";
import { MessageBubble } from "./MessageBubble";

afterEach(cleanup);

const reply = (changes: Partial<Message>): Message => ({
  id: "57",
  role: "assistant",
  content: "Not in your material.",
  citations: [],
  searched: "Searched 2 documents · 0 passages",
  ...changes,
});

describe("MessageBubble", () => {
  it("offers next steps under a refused reply", () => {
    const onAddDocuments = vi.fn();
    render(<MessageBubble message={reply({ refused: true })} onOpenSource={vi.fn()} onAddDocuments={onAddDocuments} />);

    expect(screen.getByText("Searched 2 documents · 0 passages")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Add documents" }));
    expect(onAddDocuments).toHaveBeenCalledOnce();
  });

  it("shows no next steps under an answer", () => {
    render(<MessageBubble message={reply({ content: "A grapple is… [S1]" })} onOpenSource={vi.fn()} onAddDocuments={vi.fn()} />);

    expect(screen.queryByRole("button", { name: "Add documents" })).toBeNull();
  });

  it("names a citation marker for screen readers", () => {
    const { container } = render(
      <MessageBubble message={reply({ content: "A grapple is… [S2]" })} onOpenSource={vi.fn()} onAddDocuments={vi.fn()} />,
    );

    expect(container.querySelector("sup")?.textContent).toBe("source 2");
  });
});
