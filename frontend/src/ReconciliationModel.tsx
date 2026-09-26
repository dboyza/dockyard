import { useState } from "react";
import { ArrowDown, Box, Minus, Plus, RotateCcw } from "lucide-react";

export function ReconciliationModel() {
  const [desired, setDesired] = useState(2);
  const [pods, setPods] = useState([1, 2]);
  const [nextIdentity, setNextIdentity] = useState(3);
  const [message, setMessage] = useState(
    "Two Pods match the desired count. Delete one, then advance the controller.",
  );
  const gap = desired - pods.length;
  function reconcile() {
    if (gap > 0) {
      setPods([...pods, nextIdentity]);
      setNextIdentity(nextIdentity + 1);
      setMessage(`Created Pod ${nextIdentity}. It has a new identity.`);
    } else if (gap < 0) {
      setPods(pods.slice(0, -1));
      setMessage("Removed an excess Pod to move toward the desired count.");
    } else {
      setMessage("No change needed. Observed count matches desired count.");
    }
  }
  return (
    <section
      className="reconciliation-model"
      aria-label="Explore reconciliation"
    >
      <div className="section-heading">
        <div>
          <div className="eyebrow">INTERACTIVE CONCEPT MODEL</div>
          <h3>Intent survives a missing Pod</h3>
        </div>
        <button
          className="icon"
          aria-label="Reset concept model"
          onClick={() => {
            setDesired(2);
            setPods([1, 2]);
            setNextIdentity(3);
            setMessage("Model reset. Two Pods match the desired count.");
          }}
        >
          <RotateCcw size={16} />
        </button>
      </div>
      <p className="small muted">
        A simplified model, separate from your real lab. Each controller step
        changes one Pod; real reconciliation is asynchronous.
      </p>
      <div className="desired-state">
        <span>Deployment</span>
        <div className="replica-control">
          <button
            aria-label="Decrease desired replicas"
            disabled={desired === 0}
            onClick={() => setDesired(desired - 1)}
          >
            <Minus size={14} />
          </button>
          <strong>{desired} desired</strong>
          <button
            aria-label="Increase desired replicas"
            disabled={desired === 4}
            onClick={() => setDesired(desired + 1)}
          >
            <Plus size={14} />
          </button>
        </div>
      </div>
      <div className="controller-step">
        <ArrowDown size={20} aria-hidden="true" />
        <span>Deployment → ReplicaSet → Pods</span>
        <button onClick={reconcile}>Advance controller</button>
      </div>
      <div className="model-pods" aria-label="Observed Pods">
        {pods.length ? (
          pods.map((id) => (
            <div className="model-pod" key={id}>
              <Box size={19} />
              <strong>Pod {id}</strong>
              <button
                onClick={() => {
                  setPods(pods.filter((pod) => pod !== id));
                  setMessage(
                    `Deleted Pod ${id}. The Deployment still requests ${desired} replicas.`,
                  );
                }}
                aria-label={`Delete model Pod ${id}`}
              >
                Delete
              </button>
            </div>
          ))
        ) : (
          <p className="small muted">No observed Pods.</p>
        )}
      </div>
      <div className="model-observation" role="status" aria-live="polite">
        <strong>
          {pods.length} observed / {desired} desired
        </strong>
        <span>{gap === 0 ? "Counts match." : "Reconciliation is needed."}</span>
        <p>{message}</p>
      </div>
    </section>
  );
}
