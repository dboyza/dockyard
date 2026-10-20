import { useEffect, useRef, useState, type ReactNode } from "react";
import { BookOpen, TerminalSquare } from "lucide-react";
import { TerminalDock, type DockHandle } from "./TerminalDock";
import type { Workbench } from "./useWorkbench";

type Layout = "split" | "maximized" | "collapsed";
const DEFAULT_SPLIT = 0.46;

function stored<T>(
  key: string,
  fallback: T,
  valid: (value: unknown) => boolean,
) {
  try {
    const value = JSON.parse(localStorage.getItem(key) ?? "null");
    return valid(value) ? (value as T) : fallback;
  } catch {
    return fallback;
  }
}
function store(key: string, value: unknown) {
  try {
    localStorage.setItem(key, JSON.stringify(value));
  } catch {
    // Layout preferences are a convenience; the defaults still work.
  }
}

/** Lesson or exam content beside the lab's embedded terminal, like a focused IDE. */
export function Workspace({
  model,
  unitId,
  runtime,
  retake,
  footer,
  children,
}: {
  model: Workbench;
  unitId: string;
  runtime: string;
  retake: boolean;
  footer?: ReactNode;
  children: ReactNode;
}) {
  const [split, setSplit] = useState(() =>
    stored(
      "dockyard-split",
      DEFAULT_SPLIT,
      (value) => typeof value === "number" && value >= 0.25 && value <= 0.75,
    ),
  );
  const [layout, setLayout] = useState<Layout>(() =>
    stored<Layout>("dockyard-terminal-layout", "split", (value) =>
      ["split", "maximized", "collapsed"].includes(value as string),
    ),
  );
  // Narrow screens show one pane at a time.
  const [pane, setPane] = useState<"lesson" | "terminal">("lesson");
  const [dragging, setDragging] = useState(false);
  const grid = useRef<HTMLDivElement>(null);
  const lesson = useRef<HTMLElement>(null);
  const dock = useRef<DockHandle>(null);
  const live = model.state.consoles.filter(
    (item) => item.unit_id === unitId && item.alive,
  ).length;

  useEffect(() => {
    document.body.dataset.workspace = "";
    return () => {
      delete document.body.dataset.workspace;
    };
  }, []);
  useEffect(() => store("dockyard-terminal-layout", layout), [layout]);
  useEffect(() => {
    // Ctrl+` moves between the lesson and the terminal, as in many editors.
    const toggle = (event: KeyboardEvent) => {
      if (!event.ctrlKey || event.key !== "`") return;
      event.preventDefault();
      const inTerminal = !!(event.target as HTMLElement | null)?.closest(
        ".dock",
      );
      if (inTerminal && layout !== "maximized") {
        lesson.current?.focus();
        setPane("lesson");
      } else {
        if (layout === "collapsed") setLayout("split");
        setPane("terminal");
        requestAnimationFrame(() => dock.current?.focus());
      }
    };
    window.addEventListener("keydown", toggle);
    return () => window.removeEventListener("keydown", toggle);
  }, [layout]);

  const move = (clientX: number) => {
    const box = grid.current?.getBoundingClientRect();
    if (!box) return;
    setSplit(Math.min(0.75, Math.max(0.25, (clientX - box.left) / box.width)));
  };
  const commit = (value: number) => {
    setSplit(value);
    store("dockyard-split", value);
  };

  return (
    <div
      ref={grid}
      className={`workspace ${layout} ${dragging ? "dragging" : ""} show-${pane}`}
      style={{ "--split": `${split * 100}%` } as React.CSSProperties}
    >
      <div className="workspace-switch" role="group" aria-label="Show">
        <button
          aria-pressed={pane === "lesson"}
          onClick={() => setPane("lesson")}
        >
          <BookOpen size={15} /> Lesson
        </button>
        <button
          aria-pressed={pane === "terminal"}
          onClick={() => setPane("terminal")}
        >
          <TerminalSquare size={15} /> Terminal
          {live > 0 && <span className="nav-count">{live}</span>}
        </button>
      </div>
      <section
        ref={lesson}
        className="workspace-lesson"
        tabIndex={-1}
        aria-label="Lesson"
      >
        <div className="workspace-lesson-content">{children}</div>
        {footer && <div className="workspace-footer">{footer}</div>}
      </section>
      <div
        className="workspace-splitter"
        role="separator"
        aria-orientation="vertical"
        aria-label="Resize the lesson and terminal"
        aria-valuemin={25}
        aria-valuemax={75}
        aria-valuenow={Math.round(split * 100)}
        tabIndex={0}
        onDoubleClick={() => commit(DEFAULT_SPLIT)}
        onKeyDown={(event) => {
          const step = { ArrowLeft: -0.02, ArrowRight: 0.02 }[event.key];
          if (step) {
            event.preventDefault();
            commit(Math.min(0.75, Math.max(0.25, split + step)));
          } else if (event.key === "Home") commit(0.25);
          else if (event.key === "End") commit(0.75);
          else if (event.key === "Enter") commit(DEFAULT_SPLIT);
        }}
        onPointerDown={(event) => {
          event.currentTarget.setPointerCapture(event.pointerId);
          setDragging(true);
        }}
        onPointerMove={(event) => dragging && move(event.clientX)}
        onPointerUp={(event) => {
          setDragging(false);
          event.currentTarget.releasePointerCapture(event.pointerId);
          store("dockyard-split", split);
        }}
      />
      {layout === "collapsed" ? (
        <button
          className="workspace-rail"
          onClick={() => {
            setLayout("split");
            requestAnimationFrame(() => dock.current?.focus());
          }}
          aria-label={`Show the terminal, ${live} ${live === 1 ? "shell" : "shells"} open`}
        >
          <TerminalSquare size={18} />
          <span>Terminal</span>
          {live > 0 && <span className="nav-count">{live}</span>}
        </button>
      ) : null}
      <div className="workspace-terminal">
        <TerminalDock
          ref={dock}
          model={model}
          unitId={unitId}
          runtime={runtime}
          retake={retake}
          maximized={layout === "maximized"}
          onMaximize={() =>
            setLayout(layout === "maximized" ? "split" : "maximized")
          }
          onCollapse={() => {
            setLayout("collapsed");
            lesson.current?.focus();
          }}
        />
      </div>
    </div>
  );
}
