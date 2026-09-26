import { afterEach, expect, test, vi } from "vitest";
import { api, connect } from "./api";

afterEach(() => {
  vi.unstubAllGlobals();
  history.replaceState(null, "", "/");
});

test("bootstrap removes the sign-in token before making the request", async () => {
  history.replaceState(null, "", "/#session=one-time-test-token");
  const fetch = vi.fn(async (url, init) => {
    expect(location.hash).toBe("");
    expect(url).toBe("/api/session");
    expect(JSON.parse(init.body)).toEqual({ token: "one-time-test-token" });
    expect(init.headers["X-Dockyard"]).toBe("1");
    return new Response(JSON.stringify({ connected: true }));
  });
  vi.stubGlobal("fetch", fetch);
  await connect();
  await connect();
  expect(fetch).toHaveBeenCalledTimes(1);
});

test("an error response gives the learner its actionable detail", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn(
      async () =>
        new Response(
          JSON.stringify({ detail: "Resume the lab before checking." }),
          { status: 400 },
        ),
    ),
  );
  await expect(
    api("/units/m01-processes/lab", { action: "check" }),
  ).rejects.toThrow("Resume the lab before checking.");
});

test("a disconnected or non-JSON service does not appear successful", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn(async () => new Response("Service unavailable", { status: 503 })),
  );
  await expect(api("/state")).rejects.toThrow(
    "The local service did not respond as expected.",
  );
});
