import { render, screen } from "@testing-library/react";
import { expect, test, vi } from "vitest";
import { TerminalLauncher } from "./TerminalLauncher";
import { api } from "./api";
import type { Workbench } from "./useWorkbench";

vi.mock("./api", () => ({ api: vi.fn() }));

test("terminal controls become available when workspace preparation finishes", async () => {
  let workspaceExists = false;
  vi.mocked(api).mockImplementation(async () => {
    if (!workspaceExists)
      throw new Error("Prepare the lab before opening its terminal.");
    return {
      options: [{ id: "terminal", label: "Terminal" }],
      selected: "auto",
      automatic: "Terminal",
      command: "dockyard lab shell m01-mission",
      wsl: false,
    };
  });
  const model = (state: "preparing" | "ready") =>
    ({
      state: { labs: [{ unit_id: "m01-mission", id: "practice", state }] },
      busy: state === "preparing" ? "prepare" : "",
    }) as unknown as Workbench;
  const view = render(
    <TerminalLauncher model={model("preparing")} unitId="m01-mission" />,
  );
  expect(screen.queryByRole("button", { name: "Open terminal" })).toBeNull();
  workspaceExists = true;
  view.rerender(
    <TerminalLauncher model={model("ready")} unitId="m01-mission" />,
  );
  expect(
    (
      (await screen.findByRole("button", {
        name: "Open terminal",
      })) as HTMLButtonElement
    ).disabled,
  ).toBe(false);
  expect(
    screen.queryByText("Prepare the lab before opening its terminal."),
  ).toBeNull();
  view.unmount();
});
