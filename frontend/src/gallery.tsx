// Development-only review page: `npm run dev`, then open /gallery.html.
// It shows every lesson figure, and every step of stepped figures, in one theme.
import { createRoot } from "react-dom/client";
import figures from "../../src/dockyard/content/figures.json";
import terms from "../../src/dockyard/content/reference/glossary.json";
import type { Figure } from "./contracts.gen";
import { FigureLinks, FigureText, LessonFigure } from "./figures/Figure";
import { drawings, isFigureId } from "./figures/registry";
import "./style.css";

// The API fills in defaults; the raw file omits them.
const all: Figure[] = figures.map((item) => ({
  steps: [],
  interactive: false,
  ...item,
}));
const only = new URLSearchParams(location.search).get("figure");
document.documentElement.dataset.theme =
  new URLSearchParams(location.search).get("theme") ?? "dark";

function Gallery() {
  return (
    <FigureText.Provider
      value={Object.fromEntries(all.map((item) => [item.id, item]))}
    >
      <FigureLinks.Provider
        value={{
          glossary: Object.fromEntries(
            terms.map((term) => [term.id, term.term]),
          ),
        }}
      >
        <main className="prose" style={{ maxWidth: 680, margin: "24px auto" }}>
          {all
            .filter((item) => !only || item.id === only)
            .map((item) => {
              const Drawing = isFigureId(item.id) ? drawings[item.id] : null;
              return (
                <section key={item.id} id={item.id}>
                  <h2>{item.id}</h2>
                  <LessonFigure id={item.id} />
                  {Drawing &&
                    item.steps.slice(1).map((step, index) => (
                      <div className="lesson-figure" key={step.label}>
                        <strong>
                          Step {index + 2}: {step.label}
                        </strong>
                        <div className="figure-canvas">
                          <Drawing step={index + 1} />
                        </div>
                      </div>
                    ))}
                </section>
              );
            })}
        </main>
      </FigureLinks.Provider>
    </FigureText.Provider>
  );
}

createRoot(document.getElementById("root")!).render(<Gallery />);
