import { render, screen } from "@testing-library/react";
import { expect, test } from "vitest";
import { Markdown } from "./teaching";

test("command blocks have no copy shortcut, so learners type each command", () => {
  render(
    <Markdown>
      {"Run this:\n\n```sh\ndocker ps\ncurl localhost\n```\n"}
    </Markdown>,
  );
  expect(screen.getByText(/docker ps/)).toBeTruthy();
  expect(screen.queryByRole("button", { name: /copy/i })).toBeNull();
});
