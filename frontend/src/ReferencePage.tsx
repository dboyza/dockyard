import { useState } from "react";
import { ArrowLeft, ArrowRight, BookOpen, Search } from "lucide-react";
import type { Workbench } from "./useWorkbench";
import { Markdown } from "./teaching";

export function ReferencePage({ model }: { model: Workbench }) {
  const {
    library,
    referenceFocus,
    setReferenceFocus,
    lesson,
    navigate,
    openLesson,
    catalog,
  } = model;
  const initialTerm = library?.glossary.find(
    (item) => referenceFocus === `term/${item.id}`,
  );
  const [query, setQuery] = useState(initialTerm?.term || "");
  if (!library) return null;
  const glossary = referenceFocus.startsWith("term/");
  const primer =
    library.primers.find((item) => referenceFocus === `primer/${item.id}`) ||
    library.primers[0];
  const matching =
    initialTerm && query === initialTerm.term
      ? [initialTerm]
      : library.glossary.filter((term) =>
          `${term.term} ${term.definition} ${term.watch_for}`
            .toLowerCase()
            .includes(query.trim().toLowerCase()),
        );
  return (
    <>
      <div className="page-heading">
        {lesson && (
          <button
            className="text-button muted"
            onClick={() => navigate("lesson")}
          >
            <ArrowLeft size={15} /> Return to your lesson
          </button>
        )}
        <div className="eyebrow">BACKGROUND KNOWLEDGE, WITHIN REACH</div>
        <h1>A reference you can work with.</h1>
        <p className="intro">
          Short primers for unfamiliar foundations. Clear definitions connected
          to real practice. Everything here is available locally.
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
          Foundations <span className="small">5 primers</span>
        </button>
        <button
          aria-pressed={glossary}
          className={glossary ? "primary" : ""}
          onClick={() => {
            setReferenceFocus("term/");
            setQuery("");
          }}
        >
          Glossary{" "}
          <span className="small">{library.glossary.length} terms</span>
        </button>
      </div>
      {glossary ? (
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
              <p>
                Try a shorter phrase, such as “storage”, “probe”, or “runtime”.
              </p>
              <button onClick={() => setQuery("")}>Show all terms</button>
            </div>
          )}
        </section>
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
            <Markdown>{primer.content}</Markdown>
          </article>
        </div>
      )}
    </>
  );
}
