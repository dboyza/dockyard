import { useEffect, useRef, useState } from "react";
import type { Assessment, FigureId } from "./contracts.gen";
import { currentPractice } from "./learning";
import { parseRoute, routeHash, type Route } from "./routing";
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
  | "incidents"
  | "placement"
  | "exams"
  | "review"
  | "lesson"
  | "labs"
  | "progress"
  | "settings"
  | "checkpoints"
  | "reference";
type Dialog = {
  title: string;
  body: string;
  action: () => void;
  // Optional: label the confirm button, mark it destructive, or require a typed phrase.
  confirmLabel?: string;
  danger?: boolean;
  requireText?: string;
} | null;
// Where a learner was when they followed a figure's glossary link.
type FigureReturn = {
  figure: FigureId;
  title: string;
  step: number;
  lessonId: string | null;
  primer: string | null;
};
const emptyState: State = {
  consoles: [],
  exams: [],
  exam_readiness: {},
  checkpoints: [],
  progress: {},
  labs: [],
  operations: [],
  theme: "dark",
  last_unit: null,
};

// A bookmarked address opened before signing in is kept briefly, so the
// launcher's sign-in link can open it instead of the overview.
const savedAddress = "dockyard-address-before-sign-in";
function saveAddressForSignIn() {
  if (!parseRoute(location.hash)) return;
  try {
    localStorage.setItem(
      savedAddress,
      JSON.stringify({ hash: location.hash, at: Date.now() }),
    );
  } catch {
    // Without storage the learner simply starts from the overview.
  }
}
function resumeSavedAddress() {
  try {
    const saved = JSON.parse(localStorage.getItem(savedAddress) ?? "null");
    localStorage.removeItem(savedAddress);
    if (
      saved &&
      Date.now() - saved.at < 15 * 60 * 1000 &&
      parseRoute(saved.hash) &&
      !parseRoute(location.hash)
    )
      history.replaceState(null, "", saved.hash);
  } catch {
    // An unreadable saved address is ignored.
  }
}

export function useWorkbench() {
  const [catalog, setCatalog] = useState<Catalog | null>(null);
  const [library, setLibrary] = useState<ReferenceLibrary | null>(null);
  const [referenceFocus, setReferenceFocus] = useState("primer/terminal");
  const [figureReturn, setFigureReturn] = useState<FigureReturn | null>(null);
  const [figureRestore, setFigureRestore] = useState<{
    figure: string;
    step: number;
  } | null>(null);
  const [state, setState] = useState<State>(emptyState);
  const [page, setPage] = useState<Page>("home");
  const [examId, setExamId] = useState<string | null>(null);
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
  // The fragment of a lesson the URL asked for while it is still loading.
  const urlTarget = useRef<string | null>(null);
  const currentHash = useRef("#/");
  const applyLocationRef = useRef<(course?: Catalog | null) => void>(() => {});

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
      .then(async (signedIn) => {
        if (signedIn) resumeSavedAddress();
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
        applyLocationRef.current(course);
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
      .catch((reason) => {
        if (!alive) return;
        saveAddressForSignIn();
        setError(reason.message);
      });
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
      urlTarget.current = null;
      setBusy("");
    }
    setSearch("");
    if (destination !== "reference") setFigureReturn(null);
    setPage(destination);
    setRailOpen(false);
    setError("");
    setNotice("");
    window.scrollTo({ top: 0, behavior: "instant" });
    if (destination === "labs")
      api<Doctor>("/doctor")
        .then(setDoctor)
        .catch((e) => setError(e.message));
  };
  const openReference = (focus = "primer/terminal") => {
    setReferenceFocus(focus);
    navigate("reference");
    setFigureReturn(null);
  };
  // Opens a glossary entry from a figure, remembering where to come back to.
  const openFigureTerm = (term: string, figure: FigureId, step: number) => {
    const point: FigureReturn = {
      figure,
      title: catalog?.figures.find((item) => item.id === figure)?.title ?? "",
      step,
      lessonId: page === "lesson" ? (lesson?.id ?? null) : null,
      primer:
        page === "reference" && referenceFocus.startsWith("primer/")
          ? referenceFocus.slice("primer/".length)
          : null,
    };
    setReferenceFocus(`term/${term}`);
    navigate("reference");
    setFigureReturn(point);
  };
  const returnToFigure = async () => {
    if (!figureReturn) return;
    const point = figureReturn;
    setFigureReturn(null);
    setFigureRestore({ figure: point.figure, step: point.step });
    if (point.primer) {
      setReferenceFocus(`primer/${point.primer}`);
    } else if (point.lessonId && lesson?.id === point.lessonId) {
      setTab("learn");
      navigate("lesson");
    } else if (point.lessonId) {
      await openLesson(point.lessonId);
    }
    revealFigure(point.figure);
  };
  // Waits for the figure to render, then scrolls it into view and focuses it.
  const revealFigure = (figure: string, frames = 60) => {
    const element = document.getElementById(`figure-${figure}`);
    if (!element) {
      if (frames > 0)
        requestAnimationFrame(() => revealFigure(figure, frames - 1));
      else setFigureRestore(null);
      return;
    }
    element.scrollIntoView({ block: "center", behavior: "instant" });
    element.focus({ preventScroll: true });
    element.classList.add("figure-returned");
    window.setTimeout(() => element.classList.remove("figure-returned"), 2000);
    setFigureRestore(null);
  };
  const openExam = (id: string | null) => {
    setExamId(id);
    navigate("exams");
  };
  const openLesson = async (id: string) => {
    const exam = catalog?.exams.find((item) => item.unit_id === id);
    if (exam) {
      openExam(exam.id);
      return;
    }
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
      setSearch("");
      navigate("lesson");
    } catch (reason) {
      setError((reason as Error).message);
      if (urlTarget.current !== null) {
        urlTarget.current = null;
        history.replaceState(null, "", currentHash.current);
      }
    } finally {
      if (sequence === opened.current) setBusy("");
    }
  };
  // Shows the location in the address bar: reloading, a bookmark, or the
  // browser's Back and Forward buttons.
  const applyLocation = (course: Catalog | null = catalog) => {
    let route = parseRoute(location.hash);
    if (!route) return;
    if (route.page === "lesson") {
      const unit = route.unit;
      const exam = course?.exams.find((item) => item.unit_id === unit);
      if (exam) route = { page: "exams", exam: exam.id };
      else if (!course?.units.some((item) => item.id === unit)) route = null;
    } else if (route.page === "exams" && route.exam) {
      const exam = route.exam;
      if (!course?.exams.some((item) => item.id === exam)) route = null;
    }
    if (!route) {
      history.replaceState(null, "", currentHash.current);
      return;
    }
    const target = routeHash(route);
    if (target !== location.hash) history.replaceState(null, "", target);
    if (target === currentHash.current) return;
    if (route.page === "lesson") {
      if (lesson?.id === route.unit) {
        setTab("learn");
        navigate("lesson");
      } else {
        urlTarget.current = target;
        void openLesson(route.unit);
      }
    } else if (route.page === "exams") openExam(route.exam);
    else if (route.page === "reference") {
      setReferenceFocus(route.focus);
      navigate("reference");
    } else navigate(route.page);
  };
  useEffect(() => {
    applyLocationRef.current = applyLocation;
  });
  const route: Route =
    page === "lesson"
      ? lesson
        ? { page: "lesson", unit: lesson.id }
        : { page: "home" }
      : page === "exams"
        ? { page: "exams", exam: examId }
        : page === "reference"
          ? { page: "reference", focus: referenceFocus }
          : { page };
  const hash = routeHash(route);
  // Each new location becomes a browser history entry.
  useEffect(() => {
    currentHash.current = hash;
    if (!connected || location.hash === hash) {
      if (location.hash === hash) urlTarget.current = null;
      return;
    }
    if (urlTarget.current !== null) return;
    if (parseRoute(location.hash)) history.pushState(null, "", hash);
    else history.replaceState(null, "", hash);
  }, [connected, hash]);
  useEffect(() => {
    const followHistory = () => applyLocationRef.current();
    window.addEventListener("popstate", followHistory);
    return () => window.removeEventListener("popstate", followHistory);
  }, []);
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
    terminal = "auto",
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
            ? "Your workspace will be backed up and restored to the starter. Hints and references start closed for the new attempt. Previous evidence and notes remain. Open shells restart in the fresh workspace."
            : action === "reset"
              ? "Your entire workspace will be backed up before the starter is restored. Only this lab’s owned resources are removed. Open shells restart in the fresh workspace."
              : "This removes only the resources verified as belonging to this lab, and closes its shells. Your source files and progress remain available.",
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
      const result = await api<
        Assessment & { command?: string; terminal?: string }
      >(`/units/${unitId}/lab`, { action, confirmed, terminal });
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
            ? `Opening a lab session in ${result.terminal || "your terminal"}.`
            : action === "prepare"
              ? "Your lab is ready. Its shell is open beside the lesson."
              : action === "stop"
                ? "Lab stopped. Resume it when you come back."
                : action === "resume"
                  ? "Lab resumed."
                  : action === "clean"
                    ? "Lab cleaned up."
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
      (unit) =>
        (unit.kind === "lesson" || unit.kind === "mission") &&
        !currentPractice(unit.revision, state.progress[unit.id]),
    ) ||
    units[0];
  const filtered = units.filter((unit) =>
    `${unit.search_text || ""} ${unit.id} ${unit.title} ${unit.summary} ${unit.outcomes.join(" ")}`
      .toLowerCase()
      .includes(search.trim().toLowerCase()),
  );

  return {
    examId,
    openExam,
    library,
    referenceFocus,
    setReferenceFocus,
    openReference,
    openFigureTerm,
    figureReturn,
    returnToFigure,
    figureRestore,
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
