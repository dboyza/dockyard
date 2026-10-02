import { useState } from "react";
import { ArrowLeft, ArrowRight, BookOpen, Search } from "lucide-react";
import type { GlossaryTerm } from "./api";
import type { Workbench } from "./useWorkbench";
import { Markdown } from "./teaching";

export function ReferencePage({ model }: { model: Workbench }) {
  const {
    library,
    referenceFocus,
    setReferenceFocus,
    lesson,
    navigate,
    figureReturn,
    returnToFigure,
  } = model;
  if (!library) return null;
  const glossary = referenceFocus.startsWith("term/");
  const primer =
    library.primers.find((item) => referenceFocus === `primer/${item.id}`) ||
    library.primers[0];
  return (
    <>
      <div className="page-heading">
        {(figureReturn || lesson) && (
          <div className="reference-returns">
            {figureReturn && (
              <button
                className="return-to-figure"
                onClick={() => void returnToFigure()}
              >
                <ArrowLeft size={15} /> Back to the figure “{figureReturn.title}
                ”
              </button>
            )}
            {lesson && !figureReturn?.lessonId && (
              <button
                className="text-button muted"
                onClick={() => navigate("lesson")}
              >
                <ArrowLeft size={15} /> Return to your lesson
              </button>
            )}
          </div>
        )}
        <div className="eyebrow">Reference</div>
        <h1>A reference you can work with.</h1>
        <p className="intro">
          Look up an unfamiliar word or work through a short guide. You can
          return to your lesson when you’re ready. Everything here works
          offline.
        </p>
      </div>
      <div
        className="reference-switch"
        role="group"
        aria-label="Reference section"
      >
        <button
          aria-pressed={!glossary}
          className={!glossary ? "primary" : ""}
          onClick={() => setReferenceFocus(`primer/${primer.id}`)}
        >
          Foundations{" "}
          <span className="small">{library.primers.length} primers</span>
        </button>
        <button
          aria-pressed={glossary}
          className={glossary ? "primary" : ""}
          onClick={() => setReferenceFocus("term/")}
        >
          Glossary{" "}
          <span className="small">{library.glossary.length} terms</span>
        </button>
      </div>
      {glossary ? (
        <Glossary key={referenceFocus} model={model} />
      ) : (
        <div className="reference-layout">
          <label className="reference-mobile-picker">
            <span className="eyebrow">CHOOSE A PRIMER</span>
            <select
              aria-label="Foundation primer"
              value={primer.id}
              onChange={(event) =>
                setReferenceFocus(`primer/${event.target.value}`)
              }
            >
              {library.primers.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.title} · {item.minutes} min
                </option>
              ))}
            </select>
          </label>
          <nav className="reference-index" aria-label="Foundation primers">
            {library.primers.map((item) => (
              <button
                key={item.id}
                className={item.id === primer.id ? "selected" : ""}
                aria-current={item.id === primer.id ? "page" : undefined}
                onClick={() => setReferenceFocus(`primer/${item.id}`)}
              >
                <span className="eyebrow">{item.minutes} MIN READ</span>
                <strong>{item.title}</strong>
                <span className="small muted">{item.summary}</span>
              </button>
            ))}
          </nav>
          <article
            className="panel reference-article"
            aria-label={primer.title}
          >
            <span className="eyebrow">
              FOUNDATION PRIMER · {primer.minutes} MIN
            </span>
            <Markdown key={primer.id}>{primer.content}</Markdown>
          </article>
        </div>
      )}
    </>
  );
}

// Keyed by the reference focus, so opening a term always starts from that term.
function Glossary({ model }: { model: Workbench }) {
  const { library, referenceFocus, setReferenceFocus, openLesson, catalog } =
    model;
  const terms: GlossaryTerm[] = library?.glossary ?? [];
  const initialTerm = terms.find(
    (item) => referenceFocus === `term/${item.id}`,
  );
  const [query, setQuery] = useState(initialTerm?.term || "");
  const matching =
    initialTerm && query === initialTerm.term
      ? [initialTerm]
      : terms.filter((term) =>
          `${term.term} ${term.definition} ${term.watch_for}`
            .toLowerCase()
            .includes(query.trim().toLowerCase()),
        );
  return (
    <section className="reference-glossary" aria-label="Glossary">
      <label className="reference-search">
        <Search size={18} />
        <input
          aria-label="Search glossary"
          placeholder="Find a term, behavior, or common confusion…"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
        />
      </label>
      <p className="muted small" role="status">
        {matching.length} {matching.length === 1 ? "term" : "terms"}
        {query.trim() && ` matching “${query.trim()}”`}
      </p>
      <div className="reference-terms">
        {matching.map((term) => (
          <article
            key={term.id}
            className="panel glossary-term"
            id={`term-${term.id}`}
          >
            <h2>{term.term}</h2>
            <p>{term.definition}</p>
            <p className="term-caution">
              <strong>Watch for</strong> {term.watch_for}
            </p>
            <div className="term-practice">
              <span className="eyebrow">SEE IT IN PRACTICE</span>
              {term.units.map((id) => {
                const unit = catalog?.units.find((item) => item.id === id);
                return (
                  unit && (
                    <button
                      className="text-button"
                      key={id}
                      onClick={() => void openLesson(id)}
                    >
                      {unit.title}
                      <ArrowRight size={14} />
                    </button>
                  )
                );
              })}
            </div>
            <button
              className="text-button muted"
              onClick={() => setReferenceFocus(`primer/${term.primer}`)}
            >
              <BookOpen size={15} /> Read the related primer
            </button>
          </article>
        ))}
      </div>
      {!matching.length && (
        <div className="empty-state">
          <Search size={30} />
          <h2>No matching terms.</h2>
          <p>Try a shorter phrase, such as “storage”, “probe”, or “runtime”.</p>
          <button onClick={() => setQuery("")}>Show all terms</button>
        </div>
      )}
    </section>
  );
}
