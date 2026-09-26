import type { Assessment, Lab, Unit } from "./contracts.gen";

export type Module = {
  id: number;
  title: string;
  phase: number;
  phase_title: string;
  topics: string[];
  mission: string;
};
export type UnitSummary = Pick<
  Unit,
  | "id"
  | "revision"
  | "title"
  | "summary"
  | "module"
  | "order"
  | "minutes"
  | "kind"
  | "runtime"
  | "outcomes"
> & { search_text: string };
export type Lesson = Omit<
  Unit,
  "reference" | "checks" | "prepare" | "hints"
> & { hint_count: number; attempts: Assessment[]; note: string };
export type Progress = {
  viewed: number;
  practiced: number;
  demonstrated: number;
  hints: number;
  reference: number;
  revision: number;
  review_at: string | null;
};
export type Operation = {
  id: string;
  lab_id: string;
  action: string;
  state: string;
  detail: string;
};
export type Checkpoint = {
  id: string;
  unit_id: string;
  revision: number;
  title: string;
  created_at: string;
  independent: boolean;
  hints_used: number;
  reference_revealed: boolean;
  file_count: number;
  excluded_count: number;
  archive: string;
};
export type State = {
  checkpoints: Checkpoint[];
  progress: Record<string, Progress>;
  labs: Lab[];
  operations: Operation[];
  theme: string;
  last_unit: string | null;
};
export type Catalog = { modules: Module[]; units: UnitSummary[] };
export type Doctor = {
  tools: Record<string, string | null>;
  docker_ready: boolean;
  docker_version: string | null;
  docker_error: string | null;
  free_disk_gib: number;
};

export async function api<T>(path: string, body?: unknown): Promise<T> {
  const response = await fetch(`/api${path}`, {
    method: body === undefined ? "GET" : "POST",
    headers:
      body === undefined
        ? {}
        : { "Content-Type": "application/json", "X-Dockyard": "1" },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  if (!response.ok) {
    const data = await response.json().catch(() => ({
      detail: "The local service did not respond as expected.",
    }));
    throw new Error(
      typeof data.detail === "string"
        ? data.detail
        : "Please check the request and try again.",
    );
  }
  return response.json();
}

export async function connect(): Promise<void> {
  const fragment = new URLSearchParams(window.location.hash.slice(1));
  const token = fragment.get("session");
  if (token) {
    history.replaceState(null, "", location.pathname);
    await api("/session", { token });
  }
}
