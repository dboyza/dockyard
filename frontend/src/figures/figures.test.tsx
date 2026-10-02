import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, expect, test, vi } from "vitest";
import figures from "../../../src/dockyard/content/figures.json";
import terms from "../../../src/dockyard/content/reference/glossary.json";
import type { Figure } from "../contracts.gen";
import { Markdown } from "../teaching";
import { FigureLinks, type FigureLinkOptions, FigureText } from "./Figure";
import { drawings } from "./registry";

const all: Figure[] = figures.map((item) => ({
  steps: [],
  interactive: false,
  ...item,
}));
afterEach(cleanup);

const text = Object.fromEntries(all.map((item) => [item.id, item]));
const glossary = Object.fromEntries(terms.map((term) => [term.id, term.term]));

function lesson(markdown: string, links: FigureLinkOptions = { glossary }) {
  return render(
    <FigureText.Provider value={text}>
      <FigureLinks.Provider value={links}>
        <Markdown>{markdown}</Markdown>
      </FigureLinks.Provider>
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

test("a figure links each of its terms to the glossary at the current step", () => {
  const figure = all.find(
    (item) => item.steps.length > 1 && item.terms.length > 1,
  )!;
  const openTerm = vi.fn();
  lesson(`\`\`\`figure\n${figure.id}\n\`\`\``, { glossary, openTerm });
  const list = screen.getByRole("list", {
    name: "Glossary terms in this figure",
  });
  expect(list.textContent).toBe(
    figure.terms.map((term) => glossary[term]).join(""),
  );
  fireEvent.click(screen.getByRole("button", { name: "Next step" }));
  fireEvent.click(
    screen.getByRole("button", {
      name: `${glossary[figure.terms[1]]}, glossary entry`,
    }),
  );
  expect(openTerm).toHaveBeenCalledWith(figure.terms[1], figure.id, 1);
});

test("every figure term names a glossary entry", () => {
  for (const figure of all)
    for (const term of figure.terms)
      expect(glossary[term], `${figure.id}: ${term}`).toBeTruthy();
});

test("a returning learner sees the step they left", () => {
  const figure = all.find((item) => item.steps.length > 2)!;
  lesson(`\`\`\`figure\n${figure.id}\n\`\`\``, {
    glossary,
    restore: { figure: figure.id, step: 2 },
  });
  expect(screen.getByText(figure.steps[2].text)).toBeTruthy();
});

test("without a link handler, terms are listed as text", () => {
  const figure = all[0];
  lesson(`\`\`\`figure\n${figure.id}\n\`\`\``);
  expect(screen.queryByRole("button", { name: /glossary entry/ })).toBeNull();
  expect(
    screen.getByRole("list", { name: "Glossary terms in this figure" })
      .textContent,
  ).toContain(glossary[figure.terms[0]]);
});

test("a figure keeps its step when the page around it re-renders", () => {
  const figure = all.find((item) => item.steps.length > 2)!;
  const markdown = `\`\`\`figure\n${figure.id}\n\`\`\``;
  const view = lesson(markdown);
  fireEvent.click(screen.getByRole("button", { name: "Next step" }));
  view.rerender(
    <FigureText.Provider value={{ ...text }}>
      <FigureLinks.Provider value={{ glossary: { ...glossary } }}>
        <Markdown>{markdown}</Markdown>
      </FigureLinks.Provider>
    </FigureText.Provider>,
  );
  expect(screen.getByText(figure.steps[1].text)).toBeTruthy();
});
