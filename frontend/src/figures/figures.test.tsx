import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, expect, test } from "vitest";
import figures from "../../../src/dockyard/content/figures.json";
import type { Figure } from "../contracts.gen";
import { Markdown } from "../teaching";
import { FigureText } from "./Figure";
import { drawings } from "./registry";

const all: Figure[] = figures.map((item) => ({
  steps: [],
  interactive: false,
  ...item,
}));
afterEach(cleanup);

const text = Object.fromEntries(all.map((item) => [item.id, item]));

function lesson(markdown: string) {
  return render(
    <FigureText.Provider value={text}>
      <Markdown>{markdown}</Markdown>
    </FigureText.Provider>,
  );
}

test("every drawing has teaching text and every figure has a drawing", () => {
  expect(Object.keys(drawings).sort()).toEqual(
    all.map((item) => item.id).sort(),
  );
});

test.each(all.filter((item) => !item.interactive))(
  "$id renders with an accessible description",
  (figure) => {
    lesson(`Before.\n\n\`\`\`figure\n${figure.id}\n\`\`\`\n`);
    const picture = screen.getByRole("img", { name: figure.title });
    const description = document.getElementById(
      picture.getAttribute("aria-describedby") ?? "",
    );
    expect(description?.textContent).toBe(figure.description);
    expect(screen.getByText(figure.caption)).toBeTruthy();
  },
);

test("stepped figures move between steps", () => {
  const figure = all.find((item) => item.steps.length > 2)!;
  lesson(`\`\`\`figure\n${figure.id}\n\`\`\``);
  expect(screen.getByText(figure.steps[0].label)).toBeTruthy();
  const back = screen.getByRole("button", { name: "Previous step" });
  expect((back as HTMLButtonElement).disabled).toBe(true);
  fireEvent.click(screen.getByRole("button", { name: "Next step" }));
  expect(screen.getByText(figure.steps[1].label)).toBeTruthy();
  fireEvent.click(
    screen.getByRole("button", { name: `Step 3: ${figure.steps[2].label}` }),
  );
  expect(screen.getByText(figure.steps[2].text)).toBeTruthy();
});

test("an unknown figure explains itself instead of breaking the lesson", () => {
  lesson("```figure\nno-such-figure\n```");
  expect(screen.getByRole("note").textContent).toContain(
    "not available in this version",
  );
});

test("ordinary code blocks are unaffected", () => {
  lesson("```sh\ndocker ps\n```");
  expect(screen.getByRole("button", { name: "Copy code" })).toBeTruthy();
});
