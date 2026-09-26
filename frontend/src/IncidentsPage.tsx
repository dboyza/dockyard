import { useState } from "react";
import { Search, Activity } from "lucide-react";
import type { Workbench } from "./useWorkbench";
import { UnitRow } from "./UnitRow";

export function IncidentsPage({ model }: { model: Workbench }) {
  const [query, setQuery] = useState("");
  const [runtime, setRuntime] = useState("all");
  const incidents = model.units
    .filter((unit) => unit.kind === "incident")
    .sort((a, b) => a.id.localeCompare(b.id));
  const visible = incidents.filter(
    (unit) =>
      (runtime === "all" || unit.runtime === runtime) &&
      `${unit.title} ${unit.summary} ${unit.id}`
        .toLowerCase()
        .includes(query.trim().toLowerCase()),
  );
  return (
    <>
      <div className="page-heading">
        <div className="eyebrow">INDEPENDENT DIAGNOSIS</div>
        <h1>Follow the evidence.</h1>
        <p className="intro">
          A reported symptom, a real broken environment, and room to
          investigate. Each incident has its own lab and preserves your main
          project work.
        </p>
      </div>
      <section className="panel incident-guide">
        <Activity size={24} aria-hidden="true" />
        <div>
          <h2>Diagnose. Repair. Prove.</h2>
          <p className="muted">
            Start with the symptom and preservation constraints. Use hints when
            needed, then take an independent retake to demonstrate the repair
            without them. Your observations remain part of the record.
          </p>
        </div>
      </section>
      <section className="panel" aria-label="Incident scenarios">
        <div className="incident-filters">
          <label className="searchbox">
            <Search size={17} aria-hidden="true" />
            <input
              aria-label="Search incidents"
              placeholder="Search symptoms…"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
            />
          </label>
          <label className="incident-runtime">
            Environment
            <select
              value={runtime}
              onChange={(event) => setRuntime(event.target.value)}
            >
              <option value="all">All environments</option>
              <option value="docker">Docker</option>
              <option value="kubernetes">Kubernetes</option>
              <option value="linux">Native Linux cluster</option>
            </select>
          </label>
        </div>
        <p className="muted small" role="status">
          {visible.length} of {incidents.length} scenarios
        </p>
        {visible.map((unit) => (
          <UnitRow
            key={unit.id}
            unit={unit}
            progress={model.state.progress[unit.id]}
            onOpen={model.openLesson}
          />
        ))}
        {!visible.length && (
          <p className="muted">
            No matching scenarios. Try another symptom or environment.
          </p>
        )}
      </section>
    </>
  );
}
