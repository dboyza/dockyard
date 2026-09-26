import { useState } from "react";
import { RotateCcw, Server } from "lucide-react";

export function QuorumModel() {
  const [running, setRunning] = useState([false, true, true]);
  const [backends, setBackends] = useState([true, false, false]);
  const [result, setResult] = useState(
    "Try a write through the selected endpoint.",
  );
  const voters = running.filter(Boolean).length;
  const reachable = running.some((up, index) => up && backends[index]);
  return (
    <section
      className="reconciliation-model"
      aria-label="Explore API routing and etcd quorum"
    >
      <div className="section-heading">
        <div>
          <div className="eyebrow">INTERACTIVE CONCEPT MODEL</div>
          <h3>A majority and a route are separate requirements</h3>
        </div>
        <button
          className="icon"
          aria-label="Reset quorum model"
          onClick={() => {
            setRunning([false, true, true]);
            setBackends([true, false, false]);
            setResult(
              "Model reset. Two voters survive, but the endpoint selects the failed primary.",
            );
          }}
        >
          <RotateCcw size={16} />
        </button>
      </div>
      <p className="small muted">
        This model stops an API server and its etcd voter together. All three
        voting members remain in membership. It is separate from your real lab.
      </p>
      <div className="model-pods storage-chain">
        {running.map((up, index) => (
          <div className="model-pod" key={index}>
            <Server size={20} />
            <strong>Control plane {index + 1}</strong>
            <span className="small">
              {up ? "API and voter available" : "API and voter unavailable"}
            </span>
            <button
              onClick={() => {
                setRunning(
                  running.map((state, i) => (i === index ? !state : state)),
                );
                setResult(
                  "Topology changed. Try a new write to observe its effect.",
                );
              }}
            >
              {up ? "Stop" : "Restore"} control plane {index + 1}
            </button>
            <label className="small">
              <input
                type="checkbox"
                checked={backends[index]}
                onChange={(event) => {
                  setBackends(
                    backends.map((selected, i) =>
                      i === index ? event.target.checked : selected,
                    ),
                  );
                  setResult("Endpoint selection changed. Try a new write.");
                }}
              />
              Route to control plane {index + 1}
            </label>
          </div>
        ))}
      </div>
      <p className="small">
        {voters} of 3 voters available · Majority requires 2 ·{" "}
        {reachable
          ? "A selected API is reachable"
          : "No selected API is reachable"}
      </p>
      <button
        onClick={() =>
          setResult(
            !reachable
              ? "Write failed at the endpoint. Select an available API server; an etcd majority alone cannot fix this route."
              : voters < 2
                ? "The API is reachable, but the write cannot commit. Restore a second original voter to regain the majority."
                : "The fresh write committed. The endpoint reaches a surviving API server, and two or more original voters can agree.",
          )
        }
      >
        Try a fresh write
      </button>
      <div className="model-observation" role="status" aria-live="polite">
        <p>{result}</p>
      </div>
    </section>
  );
}
