import { createRoot } from "react-dom/client";
import { useEffect, useMemo, useRef, useState } from "react";
import { useWorkbench } from "./useWorkbench";
import {
  Moon,
  ChevronRight,
  Sun,
  LoaderCircle,
  FlaskConical,
  Search,
  Container,
  LayoutDashboard,
  BookOpen,
  ShieldCheck,
  X,
  Menu,
  Library,
  Activity,
  Settings,
  Timer,
} from "lucide-react";
import { OverviewPage } from "./OverviewPage";
import { CoursePage } from "./CoursePage";
import { LessonPage } from "./LessonPage";
import { LabsPage } from "./LabsPage";
import { CheckpointsPage } from "./CheckpointsPage";
import { ReferencePage } from "./ReferencePage";
import { ProgressPage } from "./ProgressPage";
import { IncidentsPage } from "./IncidentsPage";
import { ReviewPage } from "./ReviewPage";
import { PlacementPage } from "./PlacementPage";
import { SettingsPage } from "./SettingsPage";
import { ExamsPage } from "./ExamsPage";
import { FigureLinks, FigureText } from "./figures/Figure";
import { navigationSection, pageLabels, sectionPages } from "./navigation";
import "./style.css";
import { InPageLink } from "./InPageLink";
import { parseRoute } from "./routing";
function App() {
  const model = useWorkbench();
  const figures = useMemo(
    () =>
      Object.fromEntries(
        (model.catalog?.figures ?? []).map((figure) => [figure.id, figure]),
      ),
    [model.catalog],
  );
  const glossary = useMemo(
    () =>
      Object.fromEntries(
        (model.library?.glossary ?? []).map((term) => [term.id, term.term]),
      ),
    [model.library],
  );
  const {
    page,
    setPage,
    lesson,
    search,
    setSearch,
    error,
    setError,
    notice,
    setNotice,
    connected,
    offline,
    theme,
    setTheme,
    dialog,
    setDialog,
    railOpen,
    setRailOpen,
    dialogRef,
    navigate,
  } = model;
  const section = navigationSection(page, lesson?.kind === "incident");
  const searchRef = useRef<HTMLInputElement>(null);
  useEffect(() => {
    if (!notice) return;
    const timer = window.setTimeout(() => setNotice(""), 6000);
    return () => window.clearTimeout(timer);
  }, [notice, setNotice]);
  useEffect(() => {
    const where =
      page === "lesson" && lesson
        ? lesson.title
        : page === "exams" && model.examId
          ? model.catalog?.exams.find((exam) => exam.id === model.examId)?.title
          : pageLabels[page];
    document.title = where ? `${where} · Dockyard` : "Dockyard";
  }, [page, lesson, model.examId, model.catalog]);
  const liveLabs = model.state.labs.filter(
    (item) => item.state !== "absent",
  ).length;
  useEffect(() => {
    const focusSearch = (event: KeyboardEvent) => {
      const target = event.target as HTMLElement | null;
      const typing = !!target?.closest(
        "input, textarea, select, [contenteditable]",
      );
      if (event.key === "Escape") setRailOpen(false);
      if (event.key === "/" && !typing && !event.metaKey && !event.ctrlKey) {
        event.preventDefault();
        searchRef.current?.focus();
      }
    };
    window.addEventListener("keydown", focusSearch);
    return () => window.removeEventListener("keydown", focusSearch);
  }, [setRailOpen]);
  if (!connected)
    return (
      <main className="connection">
        <div className="brand">
          <Container size={25} />
          DOCKYARD
        </div>
        <h1>
          {error ? "This browser is not connected." : "Opening your workbench…"}
        </h1>
        {error ? (
          <>
            <p>
              For your security, each browser link works once. To open Dockyard
              again, run this in your Dockyard folder:
            </p>
            <pre className="connection-command">./dockyard</pre>
            <p className="muted small">
              It opens a fresh link in your browser
              {parseRoute(location.hash)
                ? " and brings you back to this page"
                : ""}
              . Your files and progress stay on this computer. ({error})
            </p>
          </>
        ) : (
          <p>Loading your course and progress.</p>
        )}
        {!error && <LoaderCircle className="spin" />}
      </main>
    );

  return (
    <FigureText.Provider value={figures}>
      <FigureLinks.Provider
        value={{
          glossary,
          openTerm: model.openFigureTerm,
          restore: model.figureRestore,
        }}
      >
        <div className="app">
          <InPageLink className="skip" target="main">
            Skip to content
          </InPageLink>
          <aside id="sidebar" className={`sidebar ${railOpen ? "open" : ""}`}>
            <div className="sidebar-header">
              <button className="brand" onClick={() => navigate("home")}>
                <Container size={24} />
                <span>DOCKYARD</span>
              </button>
              <button
                className="icon drawer-close"
                aria-label="Close navigation"
                onClick={() => setRailOpen(false)}
              >
                <X size={20} />
              </button>
            </div>
            <nav aria-label="Main navigation">
              {(
                [
                  { id: "home", label: "Overview", icon: LayoutDashboard },
                  { id: "course", label: "Your course", icon: BookOpen },
                  { id: "incidents", label: "Practice", icon: Activity },
                  { id: "progress", label: "Your progress", icon: ShieldCheck },
                  { id: "labs", label: "Lab manager", icon: FlaskConical },
                ] as const
              ).map((item) => (
                <button
                  key={item.id}
                  className={section === item.id ? "selected" : ""}
                  aria-current={section === item.id ? "page" : undefined}
                  aria-describedby={
                    item.id === "labs" && liveLabs > 0
                      ? "live-lab-count"
                      : undefined
                  }
                  onClick={() => navigate(item.id)}
                >
                  <item.icon size={18} />
                  {item.label}
                  {item.id === "labs" && liveLabs > 0 && (
                    <span className="nav-count" aria-hidden="true">
                      {liveLabs}
                    </span>
                  )}
                </button>
              ))}
            </nav>
            {liveLabs > 0 && (
              <span id="live-lab-count" className="sr-only">
                {liveLabs} {liveLabs === 1 ? "lab" : "labs"} on this computer
              </span>
            )}
            <div className="sidebar-footer">
              <nav aria-label="Workspace tools">
                {(
                  [
                    { id: "reference", icon: Library },
                    { id: "settings", icon: Settings },
                  ] as const
                ).map((item) => (
                  <button
                    key={item.id}
                    className={page === item.id ? "selected" : ""}
                    aria-current={page === item.id ? "page" : undefined}
                    onClick={() => navigate(item.id)}
                  >
                    <item.icon size={17} />
                    {pageLabels[item.id]}
                  </button>
                ))}
              </nav>
              <span className="small muted">
                Your work stays on this computer.
              </span>
            </div>
          </aside>
          {railOpen && (
            <div
              className="scrim"
              aria-hidden="true"
              onClick={() => setRailOpen(false)}
            />
          )}
          <div className="main-shell">
            <header className="topbar">
              <div className="breadcrumb">
                <button
                  className="icon mobile-menu"
                  aria-label="Toggle navigation"
                  aria-expanded={railOpen}
                  aria-controls="sidebar"
                  onClick={() => setRailOpen(!railOpen)}
                >
                  <Menu size={20} />
                </button>
                <span className="wide-only">Workspace</span>
                <ChevronRight className="wide-only" size={14} />
                <strong>
                  {page === "lesson"
                    ? `Module ${String(lesson?.module).padStart(2, "0")}`
                    : pageLabels[page]}
                </strong>
              </div>
              <label className="searchbox">
                <Search size={16} />
                <input
                  ref={searchRef}
                  aria-label="Search lessons and terms"
                  aria-keyshortcuts="/"
                  placeholder="Search lessons and terms"
                  value={search}
                  onChange={(event) => {
                    setSearch(event.target.value);
                    setPage("course");
                    setRailOpen(false);
                  }}
                  onKeyDown={(event) => {
                    if (event.key === "Escape") {
                      setSearch("");
                      event.currentTarget.blur();
                    }
                  }}
                />
                {search ? (
                  <button
                    type="button"
                    className="icon search-clear"
                    aria-label="Clear search"
                    onClick={() => {
                      setSearch("");
                      searchRef.current?.focus();
                    }}
                  >
                    <X size={15} />
                  </button>
                ) : (
                  <kbd className="search-shortcut" aria-hidden="true">
                    /
                  </kbd>
                )}
              </label>
              <div className="topbar-actions">
                <ExamClock model={model} />
                {offline && (
                  <span className="connection-indicator offline" role="status">
                    <span />
                    Reconnecting…
                  </span>
                )}
                <button
                  className="icon"
                  aria-label={
                    theme === "dark" ? "Use light theme" : "Use dark theme"
                  }
                  onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
                >
                  {theme === "dark" ? <Sun size={19} /> : <Moon size={19} />}
                </button>
              </div>
              {model.busy && <div className="busy-bar" aria-hidden="true" />}
            </header>
            <main
              id="main"
              className={`main ${page === "lesson" ? "lesson-main" : ""}`}
            >
              {offline && (
                <div className="banner warning" role="status">
                  The local connection is interrupted. Displayed evidence may be
                  stale. Changes will resume when the service reconnects.
                </div>
              )}
              {page !== "lesson" && sectionPages[section] && (
                <nav
                  className="section-nav"
                  aria-label={`${section === "incidents" ? "Practice" : pageLabels[section]} sections`}
                >
                  {sectionPages[section]?.map((destination) => (
                    <button
                      key={destination}
                      aria-current={page === destination ? "page" : undefined}
                      onClick={() =>
                        // A section's own button opens its index, such as
                        // the exam list rather than the last exam opened.
                        destination === "exams"
                          ? model.openExam(null)
                          : navigate(destination)
                      }
                    >
                      {pageLabels[destination]}
                    </button>
                  ))}
                </nav>
              )}
              {page === "home" && <OverviewPage model={model} />}
              {page === "course" && <CoursePage model={model} />}
              {page === "placement" && <PlacementPage model={model} />}
              {page === "settings" && <SettingsPage model={model} />}
              {page === "exams" && (
                <ExamsPage key={model.examId || "exam-index"} model={model} />
              )}
              {page === "incidents" && <IncidentsPage model={model} />}
              {page === "review" && <ReviewPage model={model} />}
              {page === "lesson" && <LessonPage model={model} />}
              {page === "labs" && <LabsPage model={model} />}
              {page === "progress" && <ProgressPage model={model} />}
              {page === "checkpoints" && <CheckpointsPage model={model} />}
              {page === "reference" && <ReferencePage model={model} />}
            </main>
          </div>
          <div className="toasts">
            {error && (
              <div className="banner error" role="alert">
                <span>{error}</span>
                <button
                  className="icon"
                  aria-label="Dismiss error"
                  onClick={() => setError("")}
                >
                  <X size={17} />
                </button>
              </div>
            )}
            {notice && (
              <div className="banner success" role="status">
                <span>{notice}</span>
                <button
                  className="icon"
                  aria-label="Dismiss message"
                  onClick={() => setNotice("")}
                >
                  <X size={17} />
                </button>
              </div>
            )}
          </div>
          <dialog
            ref={dialogRef}
            onCancel={() => setDialog(null)}
            className="confirm-dialog"
          >
            {dialog && (
              <ConfirmContent
                dialog={dialog}
                onCancel={() => setDialog(null)}
              />
            )}
          </dialog>
        </div>
      </FigureLinks.Provider>
    </FigureText.Provider>
  );
}

type Confirmation = NonNullable<ReturnType<typeof useWorkbench>["dialog"]>;

// Mounted only while the dialog is open, so a typed phrase never carries over.
function ConfirmContent({
  dialog,
  onCancel,
}: {
  dialog: Confirmation;
  onCancel: () => void;
}) {
  const [typed, setTyped] = useState("");
  const blocked = !!dialog.requireText && typed.trim() !== dialog.requireText;
  return (
    <>
      <h2>{dialog.title}</h2>
      <p>{dialog.body}</p>
      {dialog.requireText && (
        <label className="confirm-phrase">
          <span>
            Type <strong>{dialog.requireText}</strong> to confirm
          </span>
          <input
            value={typed}
            autoComplete="off"
            spellCheck={false}
            onChange={(event) => setTyped(event.target.value)}
          />
        </label>
      )}
      <div className="button-row">
        <button onClick={onCancel}>Keep working</button>
        <button
          className={dialog.danger ? "danger" : "primary"}
          disabled={blocked}
          onClick={dialog.action}
        >
          {dialog.confirmLabel ?? "Continue"}
        </button>
      </div>
    </>
  );
}

function ExamClock({ model }: { model: ReturnType<typeof useWorkbench> }) {
  const active = model.state.exams.find((item) => item.state === "active");
  const [now, setNow] = useState(() => Date.now());
  useEffect(() => {
    if (!active) return;
    const timer = window.setInterval(() => setNow(Date.now()), 1000);
    return () => window.clearInterval(timer);
  }, [active]);
  if (!active || (model.page === "exams" && model.examId === active.exam_id))
    return null;
  const remaining = Math.max(
    0,
    Math.ceil((Date.parse(active.deadline) - now) / 1000),
  );
  const hours = Math.floor(remaining / 3600);
  const minutes = Math.floor((remaining % 3600) / 60);
  const seconds = remaining % 60;
  const label = `${hours}:${String(minutes).padStart(2, "0")}:${String(seconds).padStart(2, "0")}`;
  return (
    <button
      className={`exam-clock ${remaining < 600 ? "low" : ""}`}
      onClick={() => model.openExam(active.exam_id)}
      aria-label={`Practice exam in progress, ${hours} hours ${minutes} minutes left. Open the exam.`}
    >
      <Timer size={15} />
      {label}
    </button>
  );
}

createRoot(document.getElementById("root")!).render(<App />);
