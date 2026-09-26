import { useEffect, useRef, useState } from "react";
import type { Assessment } from "./contracts.gen";
import { currentPractice } from "./learning";
import {
  api,
  connect,
  type Catalog,
  type Doctor,
  type Lesson,
  type State,
  type ReferenceLibrary,
} from "./api";
export type Page =
  | "home"
  | "course"
  | "lesson"
  | "labs"
  | "progress"
  | "checkpoints"
  | "reference";
type Dialog = { title: string; body: string; action: () => void } | null;
const emptyState: State = {
  checkpoints: [],
  progress: {},
  labs: [],
  operations: [],
  theme: "dark",
  last_unit: null,
};

export function useWorkbench() {
  const [catalog, setCatalog] = useState<Catalog | null>(null);
  const [library, setLibrary] = useState<ReferenceLibrary | null>(null);
  const [referenceFocus, setReferenceFocus] = useState("primer/terminal");
  const [state, setState] = useState<State>(emptyState);
  const [page, setPage] = useState<Page>("home");
  const [lesson, setLesson] = useState<Lesson | null>(null);
  const [tab, setTab] = useState<"learn" | "mission" | "evidence">("learn");
  const [search, setSearch] = useState("");
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [connected, setConnected] = useState(false);
  const [offline, setOffline] = useState(false);
  const [busy, setBusy] = useState("");
  const [theme, setTheme] = useState(
    localStorage.getItem("dockyard-theme") || "dark",
  );
  const [hints, setHints] = useState<string[]>([]);
  const [reference, setReference] = useState<Record<string, string> | null>(
    null,
  );
  const [prediction, setPrediction] = useState<number | null>(null);
  const [predictionSubmitted, setPredictionSubmitted] = useState(false);
  const [assessment, setAssessment] = useState<Assessment | null>(null);
  const [doctor, setDoctor] = useState<Doctor | null>(null);
  const [note, setNote] = useState("");
  const [dialog, setDialog] = useState<Dialog>(null);
  const [railOpen, setRailOpen] = useState(false);
  const dialogRef = useRef<HTMLDialogElement>(null);
  const opened = useRef(0);

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    localStorage.setItem("dockyard-theme", theme);
  }, [theme]);
  useEffect(() => {
    const reconnectFromLauncher = () => {
      if (new URLSearchParams(location.hash.slice(1)).has("session"))
        location.reload();
    };
    window.addEventListener("hashchange", reconnectFromLauncher);
    return () =>
      window.removeEventListener("hashchange", reconnectFromLauncher);
  }, []);
  useEffect(() => {
    let alive = true;
    let events: EventSource | undefined;
    connect()
      .then(async () => {
        const [course, current, referenceLibrary] = await Promise.all([
          api<Catalog>("/catalog"),
          api<State>("/state"),
          api<ReferenceLibrary>("/reference"),
        ]);
        if (!alive) return;
        setCatalog(course);
        setLibrary(referenceLibrary);
        setState(current);
        setConnected(true);
        events = new EventSource("/api/events");
        events.addEventListener("state", (event) => {
          if (alive) {
            setState(JSON.parse((event as MessageEvent).data));
            setOffline(false);
          }
        });
        events.onopen = () => setOffline(false);
        events.onerror = () => setOffline(true);
      })
      .catch((reason) => alive && setError(reason.message));
    return () => {
      alive = false;
      events?.close();
    };
  }, []);
  useEffect(() => {
    if (dialog) dialogRef.current?.showModal();
    else dialogRef.current?.close();
  }, [dialog]);

  const refresh = async () => setState(await api<State>("/state"));
  const navigate = (destination: Page) => {
    if (destination !== "lesson") {
      opened.current++;
      setBusy("");
    }
    setPage(destination);
    setRailOpen(false);
    setError("");
    window.scrollTo(0, 0);
    if (destination === "labs")
      api<Doctor>("/doctor")
        .then(setDoctor)
        .catch((e) => setError(e.message));
  };
  const openReference = (focus = "primer/terminal") => {
    setReferenceFocus(focus);
    navigate("reference");
  };
  const openLesson = async (id: string) => {
    const sequence = ++opened.current;
    setBusy("Opening lesson");
    setError("");
    try {
      const next = await api<Lesson>(`/units/${id}`);
      if (sequence !== opened.current) return;
      await api(`/units/${id}/events`, { event: "viewed" });
      if (sequence !== opened.current) return;
      setLesson(next);
      setTab("learn");
      setHints([]);
      setReference(null);
      setPrediction(null);
      setPredictionSubmitted(false);
      setAssessment(next.attempts[0] || null);
      setNote(next.note);
      navigate("lesson");
    } catch (reason) {
      setError((reason as Error).message);
    } finally {
      if (sequence === opened.current) setBusy("");
    }
  };
  const lab = state.labs.find((item) => item.unit_id === lesson?.id);
  const activeOperation = state.operations.find(
    (item) =>
      item.lab_id === lab?.id &&
      ["running", "queued", "canceling"].includes(item.state),
  );
  const perform = async (
    action: string,
    confirmed = false,
    unitId = lesson?.id,
  ) => {
    if (!unitId) return;
    if (["reset", "retake", "clean"].includes(action) && !confirmed) {
      setDialog({
        title:
          action === "retake"
            ? "Start an independent retake?"
            : action === "reset"
              ? "Reset this lab?"
              : "Clean up this lab?",
        body:
          action === "retake"
            ? "Your workspace will be backed up and restored to the starter. Hints and references start closed for the new attempt. Previous evidence and notes remain. Reopen the terminal afterward."
            : action === "reset"
              ? "Your entire workspace will be backed up before the starter is restored. Only this lab’s owned resources are removed. Reopen its terminal afterward."
              : "This removes only the resources verified as belonging to this lab. Your source files and progress remain available.",
        action: () => {
          setDialog(null);
          void perform(action, true, unitId);
        },
      });
      return;
    }
    const sequence = opened.current;
    setBusy(action);
    setError("");
    setNotice("");
    try {
      const result = await api<Assessment & { command?: string }>(
        `/units/${unitId}/lab`,
        { action, confirmed },
      );
      if (sequence !== opened.current) {
        await refresh();
        return;
      }
      if (action === "check") {
        setAssessment(result);
        setTab("evidence");
      } else {
        if (action === "retake") {
          setHints([]);
          setReference(null);
          setAssessment(null);
          setTab("mission");
        }
        setNotice(
          action === "terminal"
            ? "A dedicated WezTerm lab session is opening."
            : action === "prepare"
              ? "Your workspace is ready. Open the terminal to begin."
              : `${action.charAt(0).toUpperCase() + action.slice(1)} completed.`,
        );
      }
      await refresh();
    } catch (reason) {
      if (sequence === opened.current) setError((reason as Error).message);
    } finally {
      if (sequence === opened.current) setBusy("");
    }
  };
  const revealHint = async () => {
    if (!lesson) return;
    const sequence = opened.current;
    try {
      const result = await api<{ hint: string }>(
        `/units/${lesson.id}/hints/${hints.length}`,
        {},
      );
      if (sequence === opened.current) setHints([...hints, result.hint]);
    } catch (reason) {
      setError((reason as Error).message);
    }
  };
  const revealReference = () => {
    if (!lesson) return;
    const id = lesson.id;
    const sequence = opened.current;
    setDialog({
      title: "Reveal the reference?",
      body: "Your draft stays unchanged. This attempt will count as supported practice. You can demonstrate the skill independently in a later assessment.",
      action: () => {
        setDialog(null);
        api<Record<string, string>>(`/units/${id}/reference`, {
          action: "reveal",
          confirmed: true,
        })
          .then((value) => {
            if (sequence === opened.current) setReference(value);
          })
          .catch((e) => setError(e.message));
      },
    });
  };
  const units = catalog?.units || [];
  const completed = units.filter((unit) =>
    currentPractice(unit.revision, state.progress[unit.id]),
  ).length;
  const demonstrated = units.filter(
    (unit) =>
      currentPractice(unit.revision, state.progress[unit.id]) &&
      state.progress[unit.id]?.demonstrated,
  ).length;
  const continueUnit =
    units.find((unit) => unit.id === state.last_unit) ||
    units.find(
      (unit) => !currentPractice(unit.revision, state.progress[unit.id]),
    ) ||
    units[0];
  const filtered = units.filter((unit) =>
    `${unit.search_text || ""} ${unit.id} ${unit.title} ${unit.summary} ${unit.outcomes.join(" ")}`
      .toLowerCase()
      .includes(search.trim().toLowerCase()),
  );

  return {
    library,
    referenceFocus,
    setReferenceFocus,
    openReference,
    catalog,
    setCatalog,
    state,
    setState,
    page,
    setPage,
    lesson,
    setLesson,
    tab,
    setTab,
    search,
    setSearch,
    error,
    setError,
    notice,
    setNotice,
    connected,
    setConnected,
    offline,
    setOffline,
    busy,
    setBusy,
    theme,
    setTheme,
    hints,
    setHints,
    reference,
    setReference,
    prediction,
    setPrediction,
    predictionSubmitted,
    setPredictionSubmitted,
    assessment,
    setAssessment,
    doctor,
    setDoctor,
    note,
    setNote,
    dialog,
    setDialog,
    railOpen,
    setRailOpen,
    dialogRef,
    opened,
    refresh,
    navigate,
    openLesson,
    lab,
    activeOperation,
    perform,
    revealHint,
    revealReference,
    units,
    completed,
    demonstrated,
    continueUnit,
    filtered,
  };
}
export type Workbench = ReturnType<typeof useWorkbench>;
