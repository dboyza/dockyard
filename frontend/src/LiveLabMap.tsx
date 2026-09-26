import { useEffect, useState } from "react";
import { ArrowRight, RefreshCw } from "lucide-react";
import { api } from "./api";
import type { LabObservation, ObservedResource } from "./contracts.gen";

const groups = [
  { title: "Traffic & networks", kinds: ["Service", "Network"] },
  {
    title: "Controllers",
    kinds: ["Deployment", "ReplicaSet", "StatefulSet", "DaemonSet"],
  },
  { title: "Running work", kinds: ["Pod", "Container"] },
  {
    title: "Persistent storage",
    kinds: ["PersistentVolumeClaim", "PersistentVolume", "Volume"],
  },
];

export function LiveLabMap({
  unitId,
  labState,
}: {
  unitId: string;
  labState?: string;
}) {
  const [snapshot, setSnapshot] = useState<LabObservation | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [revision, setRevision] = useState(0);
  const [selection, setSelection] = useState("");
  useEffect(() => {
    let active = true;
    let timer: ReturnType<typeof setTimeout>;
    const refresh = async () => {
      setLoading(true);
      try {
        const next = await api<LabObservation>(`/units/${unitId}/observation`);
        if (!active) return;
        if (next.status === "observed") {
          setSnapshot(next);
          setError("");
        } else setError(next.message);
      } catch (reason) {
        if (active) setError((reason as Error).message);
      } finally {
        if (active) {
          setLoading(false);
          timer = setTimeout(() => void refresh(), 8000);
        }
      }
    };
    void refresh();
    return () => {
      active = false;
      clearTimeout(timer);
    };
  }, [unitId, revision, labState]);
  const resources = snapshot?.resources ?? [];
  const selected = resources.find((item) => item.id === selection);
  const links =
    snapshot?.links.filter(
      (link) => link.source === selected?.id || link.target === selected?.id,
    ) ?? [];
  const connected = new Set(
    links.flatMap((link) => [link.source, link.target]),
  );
  const byId = new Map(resources.map((resource) => [resource.id, resource]));
  const label = (item: ObservedResource) =>
    `${item.kind} ${item.namespace ? item.namespace + "/" : ""}${item.name}`;
  return (
    <section className="live-lab-map" aria-label="Observed lab resources">
      <div className="live-map-heading">
        <div>
          <span className="eyebrow">YOUR ACTUAL LAB</span>
          <h2>Follow the resource relationships.</h2>
          <p>
            Inspect ownership, ready endpoints, network connections, and storage
            bindings.
          </p>
        </div>
        <button
          className="secondary"
          disabled={loading}
          onClick={() => setRevision((value) => value + 1)}
          aria-label="Refresh resource observation"
        >
          <RefreshCw size={15} /> {loading ? "Observing…" : "Refresh"}
        </button>
      </div>
      <p className={`live-map-status ${error ? "stale" : ""}`} role="status">
        {snapshot
          ? `${error ? "Last successful observation" : "Observed"} at ${new Date(snapshot.observed_at).toLocaleTimeString()}. `
          : ""}
        {error ||
          (snapshot
            ? `${resources.length} resources. Refreshes every 8 seconds while open.`
            : "Reading the local runtime…")}
      </p>
      {resources.length > 0 && (
        <>
          <div className="live-map-columns">
            {groups.map((group) => {
              const items = resources.filter((item) =>
                group.kinds.includes(item.kind),
              );
              if (!items.length) return null;
              return (
                <div className="live-map-column" key={group.title}>
                  <h3>
                    {group.title} <span>{items.length}</span>
                  </h3>
                  <div className="live-map-resources">
                    {items.map((item) => (
                      <button
                        key={item.id}
                        className={`resource-node ${selected?.id === item.id ? "selected" : ""} ${connected.has(item.id) ? "related" : ""}`}
                        aria-pressed={selected?.id === item.id}
                        onClick={() => setSelection(item.id)}
                        aria-label={label(item)}
                      >
                        <span className="resource-kind">{item.kind}</span>
                        <strong>{item.name}</strong>
                        {item.namespace && (
                          <span className="resource-namespace">
                            {item.namespace}
                          </span>
                        )}
                        <span className="resource-state">{item.state}</span>
                        <span className="resource-summary">{item.summary}</span>
                      </button>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>
          <div className="resource-connections" aria-live="polite">
            {selected ? (
              <>
                <h3>{selected.name}</h3>
                <p>
                  {selected.kind} ·{" "}
                  {selected.namespace || "Cluster or host scope"} ·{" "}
                  {selected.state}
                </p>
                {links.length ? (
                  <ul>
                    {links.map((link, index) => {
                      const source = byId.get(link.source);
                      const target = byId.get(link.target);
                      if (!source || !target) return null;
                      return (
                        <li key={`${link.source}-${link.target}-${index}`}>
                          <button onClick={() => setSelection(source.id)}>
                            {source.name}
                          </button>
                          <span>
                            <ArrowRight size={14} aria-hidden="true" />{" "}
                            {link.relation}
                          </span>
                          <button onClick={() => setSelection(target.id)}>
                            {target.name}
                          </button>
                        </li>
                      );
                    })}
                  </ul>
                ) : (
                  <p>
                    No observed relationship connects this resource to another
                    item in this map.
                  </p>
                )}
              </>
            ) : (
              <p>
                Select a resource to trace its observed relationships. This map
                reads runtime state; it does not award lesson completion.
              </p>
            )}
          </div>
        </>
      )}
    </section>
  );
}
