import {
  useEffect,
  useImperativeHandle,
  useRef,
  useState,
  type Ref,
} from "react";
import {
  Copy,
  Ellipsis,
  Eraser,
  LoaderCircle,
  Maximize2,
  Minimize2,
  Minus,
  PanelRightClose,
  Play,
  Plus,
  RefreshCw,
  Search,
  Square,
  TerminalSquare,
  Trash2,
  X,
} from "lucide-react";
import { api, type ConsoleSession } from "./api";
import { ConsoleView, type ConsoleHandle } from "./ConsoleView";
import { TerminalLauncher } from "./TerminalLauncher";
import type { Workbench } from "./useWorkbench";

export type DockHandle = { focus: () => void };
const PER_LAB = 6;
const SIZES = [11, 12, 13, 14, 15, 16, 18, 20];
const RUNTIMES: Record<string, string> = {
  docker: "Docker lab",
  kubernetes: "Kubernetes lab",
  linux: "Linux VM lab",
};

// Start shells at the pane's real size; a wider guess makes zsh's line-end marker wrap.
function paneSize(body: HTMLElement | null, fontSize: number) {
  if (!body?.clientWidth) return { cols: 80, rows: 24 };
  return {
    cols: Math.max(
      20,
      Math.floor((body.clientWidth - 36) / (fontSize * 0.6)) - 1,
    ),
    rows: Math.max(
      5,
      Math.floor((body.clientHeight - 16) / Math.ceil(fontSize * 1.25)),
    ),
  };
}

function storedSize() {
  try {
    const size = Number(localStorage.getItem("dockyard-terminal-size"));
    return SIZES.includes(size) ? size : 13;
  } catch {
    return 13;
  }
}

export function TerminalDock({
  model,
  unitId,
  runtime,
  retake,
  maximized,
  onMaximize,
  onCollapse,
  ref,
}: {
  model: Workbench;
  unitId: string;
  runtime: string;
  retake: boolean;
  maximized: boolean;
  onMaximize: () => void;
  onCollapse: () => void;
  ref?: Ref<DockHandle>;
}) {
  const { state, theme, busy, perform, setError, setNotice, refresh } = model;
  const lab = state.labs.find((item) => item.unit_id === unitId);
  const operation = state.operations.find(
    (item) =>
      item.lab_id === lab?.id &&
      ["running", "queued", "canceling"].includes(item.state),
  );
  const sessions = state.consoles
    .filter((item) => item.unit_id === unitId)
    .sort((a, b) => a.number - b.number);
  const [selected, setSelected] = useState<string | null>(null);
  const [titles, setTitles] = useState<Record<string, string>>({});
  const [fontSize, setFontSize] = useState(storedSize);
  const [menu, setMenu] = useState(false);
  const handles = useRef(new Map<string, ConsoleHandle>());
  const opening = useRef(false);
  // Closing the last tab is deliberate, so it is not reopened automatically.
  const [dismissed, setDismissed] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);
  const body = useRef<HTMLDivElement>(null);
  const current =
    sessions.find((item) => item.id === selected) ??
    sessions.filter((item) => item.alive).at(-1) ??
    sessions.at(-1);
  const live = sessions.filter((item) => item.alive).length;
  const ready = lab?.state === "ready";

  useImperativeHandle(ref, () => ({
    focus: () => current && handles.current.get(current.id)?.focus(),
  }));

  // Resolves to the shell's ID, or null when another request is already opening one.
  // An automatic open reuses the lab's live shell, so several tabs never race.
  const createShell = async (reuse = false) => {
    if (opening.current) return null;
    opening.current = true;
    try {
      // Shells Dockyard ended for a reset or cleanup are replaced, not kept as tabs.
      await Promise.all(
        sessions
          .filter((item) => !item.alive && item.ended_by)
          .map((item) => api(`/consoles/${item.id}/close`, {})),
      );
      const created = await api<ConsoleSession>(`/units/${unitId}/consoles`, {
        ...paneSize(body.current, fontSize),
        reuse,
      });
      await refresh();
      return created.id;
    } finally {
      opening.current = false;
    }
  };
  const open = () =>
    createShell()
      .then((id) => {
        if (!id) return;
        setDismissed(false);
        setSelected(id);
      })
      .catch((error) => setError((error as Error).message));
  const close = async (session: ConsoleSession) => {
    if (sessions.length === 1) setDismissed(true);
    try {
      await api(`/consoles/${session.id}/close`, {});
      await refresh();
    } catch (error) {
      setError((error as Error).message);
    }
  };

  // Open a shell for a fresh lab, and replace shells a reset or cleanup ended.
  const needsShell =
    ready &&
    !dismissed &&
    !live &&
    (!sessions.length || sessions.some((item) => item.ended_by));
  useEffect(() => {
    if (!needsShell) return;
    let alive = true;
    createShell(true)
      .then((id) => alive && id && setSelected(id))
      .catch((error) => setError((error as Error).message));
    return () => {
      alive = false;
    };
    // createShell reads the latest sessions; only a change in need should trigger it.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [needsShell]);

  useEffect(() => {
    document
      .getElementById(`console-tab-${current?.id}`)
      ?.scrollIntoView({ block: "nearest", inline: "nearest" });
  }, [current?.id]);
  useEffect(() => {
    try {
      localStorage.setItem("dockyard-terminal-size", String(fontSize));
    } catch {
      // The size simply resets next time.
    }
  }, [fontSize]);
  useEffect(() => {
    if (!menu) return;
    const dismiss = (event: Event) => {
      if (event instanceof KeyboardEvent && event.key !== "Escape") return;
      if (
        event instanceof PointerEvent &&
        menuRef.current?.contains(event.target as Node)
      )
        return;
      setMenu(false);
    };
    window.addEventListener("pointerdown", dismiss);
    window.addEventListener("keydown", dismiss);
    return () => {
      window.removeEventListener("pointerdown", dismiss);
      window.removeEventListener("keydown", dismiss);
    };
  }, [menu]);

  const resize = (step: number) =>
    setFontSize(
      (size) =>
        SIZES[
          Math.max(0, Math.min(SIZES.length - 1, SIZES.indexOf(size) + step))
        ],
    );
  const act = (action: string) => {
    setMenu(false);
    void perform(action, false, unitId);
  };

  return (
    <section className="dock" aria-label="Lab terminal">
      <header className="dock-bar">
        <div className="dock-tabs">
          <div className="dock-tablist" role="tablist" aria-label="Lab shells">
            {sessions.map((session, index) => (
              <button
                key={session.id}
                role="tab"
                id={`console-tab-${session.id}`}
                className={`dock-tab ${current?.id === session.id ? "selected" : ""}`}
                aria-controls={`console-${session.id}`}
                aria-selected={current?.id === session.id}
                aria-keyshortcuts="Delete"
                tabIndex={current?.id === session.id ? 0 : -1}
                onClick={() => setSelected(session.id)}
                onKeyDown={(event) => {
                  if (event.key === "Delete" || event.key === "Backspace") {
                    event.preventDefault();
                    void close(session);
                    return;
                  }
                  const next = {
                    ArrowRight: (index + 1) % sessions.length,
                    ArrowLeft: (index - 1 + sessions.length) % sessions.length,
                    Home: 0,
                    End: sessions.length - 1,
                  }[event.key];
                  if (next === undefined) return;
                  event.preventDefault();
                  setSelected(sessions[next].id);
                  document
                    .getElementById(`console-tab-${sessions[next].id}`)
                    ?.focus();
                }}
              >
                <span
                  className={`dock-dot ${session.alive ? "live" : ""}`}
                  aria-hidden="true"
                />
                Terminal {session.number}
                {titles[session.id] && session.alive && (
                  <span className="dock-title">{titles[session.id]}</span>
                )}
                {/* A pointer shortcut; keyboard users press Delete on the tab. */}
                <span
                  className="dock-close"
                  aria-hidden="true"
                  title="Close"
                  onClick={(event) => {
                    event.stopPropagation();
                    void close(session);
                  }}
                >
                  <X size={13} />
                </span>
              </button>
            ))}
          </div>
          <button
            className="icon dock-new"
            aria-label="Open another shell"
            title="New shell"
            disabled={!ready || live >= PER_LAB}
            onClick={() => void open()}
          >
            <Plus size={16} />
          </button>
        </div>
        <div className="dock-actions">
          {lab && (
            <span
              className={`dock-lab ${lab.state}`}
              title={`Shells here use lab ${lab.id.slice(0, 12)} only`}
            >
              <span className="dock-dot" aria-hidden="true" />
              {RUNTIMES[runtime] ?? "Lab"}
              <code>{lab.id.slice(0, 8)}</code>
            </span>
          )}
          <button
            className="icon"
            aria-label="Find in terminal"
            title={`Find (${navigator.platform.includes("Mac") ? "⌘F" : "Ctrl+Shift+F"})`}
            disabled={!current}
            onClick={() => current && handles.current.get(current.id)?.find()}
          >
            <Search size={15} />
          </button>
          <button
            className="icon dock-layout"
            aria-label={maximized ? "Show the lesson" : "Maximize the terminal"}
            title={maximized ? "Restore" : "Maximize"}
            onClick={onMaximize}
          >
            {maximized ? <Minimize2 size={15} /> : <Maximize2 size={15} />}
          </button>
          <div className="dock-menu-anchor" ref={menuRef}>
            <button
              className="icon"
              aria-label="Terminal and lab options"
              aria-expanded={menu}
              aria-haspopup="dialog"
              onClick={() => setMenu(!menu)}
            >
              <Ellipsis size={16} />
            </button>
            {menu && (
              <div
                className="dock-menu"
                role="dialog"
                aria-label="Terminal and lab options"
              >
                <div className="dock-menu-row">
                  <span>Text size</span>
                  <span className="dock-stepper">
                    <button
                      className="icon"
                      aria-label="Smaller text"
                      disabled={fontSize === SIZES[0]}
                      onClick={() => resize(-1)}
                    >
                      <Minus size={14} />
                    </button>
                    <output aria-live="polite">{fontSize}</output>
                    <button
                      className="icon"
                      aria-label="Larger text"
                      disabled={fontSize === SIZES.at(-1)}
                      onClick={() => resize(1)}
                    >
                      <Plus size={14} />
                    </button>
                  </span>
                </div>
                <button
                  className="dock-menu-item"
                  disabled={!current}
                  onClick={() => {
                    setMenu(false);
                    if (current) handles.current.get(current.id)?.clear();
                  }}
                >
                  <Eraser size={15} /> Clear scrollback
                </button>
                <hr />
                <div className="eyebrow">Lab</div>
                {lab && lab.state !== "absent" && (
                  <>
                    <button
                      className="dock-menu-item"
                      disabled={!!busy}
                      onClick={() =>
                        act(lab.state === "stopped" ? "resume" : "stop")
                      }
                    >
                      {lab.state === "stopped" ? (
                        <Play size={15} />
                      ) : (
                        <Square size={14} />
                      )}
                      {lab.state === "stopped" ? "Resume lab" : "Stop lab"}
                    </button>
                    <button
                      className="dock-menu-item"
                      disabled={!!busy}
                      onClick={() => act("reset")}
                    >
                      <RefreshCw size={14} /> Reset lab
                    </button>
                    {retake && (
                      <button
                        className="dock-menu-item"
                        disabled={!!busy}
                        onClick={() => act("retake")}
                      >
                        <RefreshCw size={14} /> Independent retake
                      </button>
                    )}
                    <button
                      className="dock-menu-item danger"
                      disabled={!!busy}
                      onClick={() => act("clean")}
                    >
                      <Trash2 size={14} /> Clean up lab
                    </button>
                    <details className="dock-menu-details">
                      <summary>Workspace location</summary>
                      <p className="mono">{lab.workspace}</p>
                      <button
                        className="small-button"
                        onClick={() =>
                          navigator.clipboard
                            .writeText(lab.workspace)
                            .then(() => setNotice("Workspace path copied."))
                            .catch(() =>
                              setError(
                                "Clipboard unavailable. Select and copy the displayed path.",
                              ),
                            )
                        }
                      >
                        <Copy size={13} /> Copy path
                      </button>
                    </details>
                  </>
                )}
                <details className="dock-menu-details">
                  <summary>Use your own terminal</summary>
                  <p className="small muted">
                    Prefer another app? Open a lab session there instead.
                  </p>
                  <TerminalLauncher model={model} unitId={unitId} />
                </details>
              </div>
            )}
          </div>
          <button
            className="icon dock-layout"
            aria-label="Hide the terminal"
            title="Hide terminal"
            onClick={onCollapse}
          >
            <PanelRightClose size={16} />
          </button>
        </div>
      </header>
      {lab?.state === "stopped" && (
        <div className="dock-banner" role="status">
          The lab is stopped. Commands that reach Docker or the cluster will
          fail until you resume it.
          <button
            className="small-button"
            disabled={!!busy}
            onClick={() => act("resume")}
          >
            <Play size={13} /> Resume
          </button>
        </div>
      )}
      {lab?.state === "failed" && (
        <div className="dock-banner danger" role="alert">
          <span>{lab.error || "The lab needs attention."}</span>
          <button
            className="small-button"
            disabled={!!busy}
            onClick={() => act("prepare")}
          >
            <RefreshCw size={13} /> Prepare lab
          </button>
        </div>
      )}
      <div className="dock-body" ref={body}>
        {sessions.map((session) => (
          <ConsoleView
            key={session.id}
            ref={(handle) => {
              if (handle) handles.current.set(session.id, handle);
              else handles.current.delete(session.id);
            }}
            session={session}
            active={current?.id === session.id}
            theme={theme}
            fontSize={fontSize}
            onTitle={(title) =>
              setTitles((known) => ({ ...known, [session.id]: title }))
            }
            onRestart={() => void open()}
            onClose={() => void close(session)}
          />
        ))}
        {(lab?.state === "preparing" || (!sessions.length && !ready)) && (
          <div className="dock-empty" role="status">
            <LoaderCircle className="spin" size={22} />
            <strong>
              {lab?.state === "preparing"
                ? `Preparing the ${RUNTIMES[runtime] ?? "lab"}`
                : "Waiting for the lab"}
            </strong>
            <span>
              {lab?.resources.stage ||
                "Your shell opens here as soon as the lab is ready."}
            </span>
            {operation && (
              <button
                className="small-button"
                onClick={() =>
                  void api(`/operations/${operation.id}/cancel`, {})
                }
              >
                Cancel preparation
              </button>
            )}
          </div>
        )}
        {!sessions.length && ready && (
          <div className="dock-empty">
            <TerminalSquare size={26} />
            <strong>No shell is open</strong>
            <span>Shells start in this lab’s workspace with its settings.</span>
            <button className="primary" onClick={() => void open()}>
              <Plus size={15} /> Open a shell
            </button>
          </div>
        )}
      </div>
    </section>
  );
}
