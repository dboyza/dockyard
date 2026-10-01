import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { expect, test, vi } from "vitest";
import { Markdown } from "./teaching";

test("command blocks copy their exact text", async () => {
  const writeText = vi.fn().mockResolvedValue(undefined);
  Object.assign(navigator, { clipboard: { writeText } });
  render(
    <Markdown>
      {"Run this:\n\n```sh\ndocker ps\ncurl localhost\n```\n"}
    </Markdown>,
  );
  fireEvent.click(screen.getByRole("button", { name: "Copy code" }));
  await waitFor(() =>
    expect(writeText).toHaveBeenCalledWith("docker ps\ncurl localhost"),
  );
  expect(await screen.findByRole("button", { name: "Copied" })).toBeTruthy();
});
