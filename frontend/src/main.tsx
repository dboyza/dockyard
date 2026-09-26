import { createRoot } from "react-dom/client";
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
} from "lucide-react";
import { OverviewPage } from "./OverviewPage";
import { CoursePage } from "./CoursePage";
import { LessonPage } from "./LessonPage";
import { LabsPage } from "./LabsPage";
import { ProgressPage } from "./ProgressPage";
import "./style.css";
function App() {
  const model = useWorkbench();
  const {
    catalog,
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
  if (!connected)
    return (
      <main className="connection">
        <div className="brand">
          <Container size={25} />
          DOCKYARD
        </div>
        <h1>
          {error ? "Connect your workbench." : "Preparing your workbench."}
        </h1>
        <p>{error || "Loading your local course and progress."}</p>
        {error && (
          <p className="muted">
            Launch Dockyard from your terminal to open a fresh one-time browser
            connection. Your files and progress are stored locally.
          </p>
        )}
        {!error && <LoaderCircle className="spin" />}
      </main>
    );

  return (
    <div className="app">
      <a className="skip" href="#main">
        Skip to content
      </a>
      <aside className={`sidebar ${railOpen ? "open" : ""}`}>
        <button className="brand" onClick={() => navigate("home")}>
          <Container size={24} />
          <span>DOCKYARD</span>
        </button>
        <div className="localtag">
          <span /> LOCAL WORKBENCH
        </div>
        <label className="searchbox">
          <Search size={16} />
          <input
            aria-label="Search lessons"
            placeholder="Find a lesson…"
            value={search}
            onChange={(event) => {
              setSearch(event.target.value);
              setPage("course");
            }}
          />
        </label>
        <nav aria-label="Main navigation">
          {(
            [
              { id: "home", label: "Overview", icon: LayoutDashboard },
              { id: "course", label: "Your course", icon: BookOpen },
              { id: "progress", label: "Skill evidence", icon: ShieldCheck },
              { id: "labs", label: "Lab manager", icon: FlaskConical },
            ] as const
          ).map((item) => (
            <button
              key={item.id}
              className={
                page === item.id || (item.id === "course" && page === "lesson")
                  ? "selected"
                  : ""
              }
              onClick={() => navigate(item.id)}
            >
              <item.icon size={18} />
              {item.label}
            </button>
          ))}
        </nav>
        <div className="sidebar-section">
          <span className="eyebrow">LEARNING PATH</span>
          {[...new Set(catalog?.modules.map((item) => item.phase_title))].map(
            (phase, index) => (
              <button
                className="phase-nav"
                key={phase}
                onClick={() => {
                  setSearch("");
                  navigate("course");
                  setTimeout(
                    () =>
                      document
                        .getElementById(`phase-${index + 1}`)
                        ?.scrollIntoView({ behavior: "smooth" }),
                    0,
                  );
                }}
              >
                <span>0{index + 1}</span>
                {phase}
              </button>
            ),
          )}
        </div>
        <div className="sidebar-footer">
          <div className="learner-avatar">D</div>
          <div>
            <strong>Personal workspace</strong>
            <span className="muted small">Progress stays on this Mac</span>
          </div>
        </div>
      </aside>
      <div className="main-shell">
        <header className="topbar">
          <div className="breadcrumb">
            <button
              className="icon mobile-menu"
              aria-label="Toggle navigation"
              onClick={() => setRailOpen(!railOpen)}
            >
              <Menu size={20} />
            </button>
            <span>Workspace</span>
            <ChevronRight size={14} />
            <strong>
              {page === "lesson"
                ? `Module ${String(lesson?.module).padStart(2, "0")}`
                : page === "home"
                  ? "Overview"
                  : page === "course"
                    ? "Your course"
                    : page === "labs"
                      ? "Lab manager"
                      : "Skill evidence"}
            </strong>
          </div>
          <div className="topbar-actions">
            <span
              className={`connection-indicator ${offline ? "offline" : ""}`}
            >
              <span />
              {offline ? "Reconnecting" : "Local connection"}
            </span>
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
          {page === "home" && <OverviewPage model={model} />}
          {page === "course" && <CoursePage model={model} />}
          {page === "lesson" && <LessonPage model={model} />}
          {page === "labs" && <LabsPage model={model} />}
          {page === "progress" && <ProgressPage model={model} />}
        </main>
        <footer className="app-footer">
          <span>Local by design. Real by practice.</span>
          <span>Dockyard · Personal workbench</span>
        </footer>
      </div>
      <dialog
        ref={dialogRef}
        onCancel={() => setDialog(null)}
        className="confirm-dialog"
      >
        <h2>{dialog?.title}</h2>
        <p>{dialog?.body}</p>
        <div className="button-row">
          <button onClick={() => setDialog(null)}>Keep working</button>
          <button className="primary" onClick={() => dialog?.action()}>
            Continue
          </button>
        </div>
      </dialog>
    </div>
  );
}

createRoot(document.getElementById("root")!).render(<App />);
