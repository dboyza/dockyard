import { coursePhases, currentPractice, glossaryMatches } from "./learning";
import { UnitRow } from "./UnitRow";
import type { Workbench } from "./useWorkbench";
import { ArrowRight, BookOpen, ChevronDown } from "lucide-react";
import type { UnitSummary } from "./api";
export function CoursePage({ model }: { model: Workbench }) {
  const {
    catalog,
    lesson,
    search,
    units,
    filtered,
    state,
    openLesson,
    continueUnit,
    library,
    openReference,
  } = model;
  const terms = glossaryMatches(library?.glossary ?? [], search);
  const openModule = lesson?.module ?? continueUnit?.module ?? 0;
  const phases = coursePhases(catalog?.modules ?? []);
  const unitRow = (unit: UnitSummary) => (
    <UnitRow
      key={unit.id}
      unit={unit}
      progress={state.progress[unit.id]}
      onOpen={openLesson}
    />
  );
  return (
    <>
      <div className="page-heading">
        <div className="eyebrow">THE COMPLETE LEARNING PATH</div>
        <h1>Your course</h1>
        <p className="intro">
          Start with the first lesson, or choose a topic you want to practise.
          Each module ends with a mission where you try the skills without
          step-by-step instructions.
        </p>
      </div>
      {!search && (
        <nav className="phase-jump" aria-label="Course phases">
          {phases.map((item) => (
            <a key={item.phase} href={`#phase-${item.phase}`}>
              <span>0{item.phase}</span>
              {item.title}
            </a>
          ))}
        </nav>
      )}
      {search ? (
        <section className="panel">
          <div className="section-heading">
            <h2>Search results</h2>
            <span className="muted small" role="status">
              {filtered.length === 1
                ? "1 lesson"
                : `${filtered.length} lessons`}
              {terms.length > 0 &&
                ` and ${terms.length === 1 ? "1 glossary term" : `${terms.length} glossary terms`}`}{" "}
              for “{search}”
            </span>
          </div>
          {terms.length > 0 && (
            <div
              className="search-terms"
              aria-label="Glossary matches"
              role="group"
            >
              <div className="search-terms-heading">
                <span className="eyebrow">
                  <BookOpen size={13} aria-hidden="true" /> In the glossary
                </span>
                <button
                  className="text-button"
                  onClick={() =>
                    openReference(`term/?${encodeURIComponent(search.trim())}`)
                  }
                >
                  {terms.length === 1
                    ? "Open in the glossary"
                    : `All ${terms.length} matching terms`}
                  <ArrowRight size={14} />
                </button>
              </div>
              <ul>
                {terms.slice(0, 4).map((term) => (
                  <li key={term.id}>
                    <button
                      className="search-term"
                      onClick={() => openReference(`term/${term.id}`)}
                    >
                      <strong>{term.term}</strong>
                      <span>{term.definition}</span>
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          )}
          {filtered.length ? (
            filtered.map((unit) => (
              <UnitRow
                key={unit.id}
                unit={unit}
                progress={state.progress[unit.id]}
                onOpen={openLesson}
                showModule
              />
            ))
          ) : (
            <p className="muted">
              No lessons match “{search}”. Try a concept such as container,
              storage, or networking.
            </p>
          )}
        </section>
      ) : (
        phases.map(({ phase, title }) => (
          <section className="course-phase" id={`phase-${phase}`} key={phase}>
            <div className="section-heading">
              <h2>
                <span className="phase-number">0{phase}</span>
                {title}
              </h2>
            </div>
            {catalog?.modules
              .filter((module) => module.phase === phase)
              .map((module) => {
                const moduleUnits = units.filter(
                  (unit) =>
                    unit.module === module.id &&
                    (unit.kind === "lesson" || unit.kind === "mission"),
                );
                const done = moduleUnits.filter((unit) =>
                  currentPractice(unit.revision, state.progress[unit.id]),
                ).length;
                return (
                  <details
                    className="module"
                    key={module.id}
                    open={module.id === openModule}
                  >
                    <summary>
                      <span className="module-id">
                        {String(module.id).padStart(2, "0")}
                      </span>
                      <span>
                        <strong>{module.title}</strong>
                        <span className="muted small">
                          {module.topics.join(" · ")}
                        </span>
                      </span>
                      {moduleUnits.length > 0 && (
                        <span
                          className="module-progress"
                          aria-label={`${done} of ${moduleUnits.length} activities practised`}
                        >
                          <span
                            className="module-progress-bar"
                            aria-hidden="true"
                          >
                            <span
                              style={{
                                width: `${(done / moduleUnits.length) * 100}%`,
                              }}
                            />
                          </span>
                          {done}/{moduleUnits.length}
                        </span>
                      )}
                      <ChevronDown size={17} />
                    </summary>
                    <div className="module-lessons">
                      {moduleUnits.map(unitRow)}
                      {!units.some((unit) => unit.module === module.id) && (
                        <p className="development-note">
                          This module is being authored in the current
                          development build.
                        </p>
                      )}
                    </div>
                  </details>
                );
              })}
          </section>
        ))
      )}
    </>
  );
}
