import { useState } from "react";
import { Box, Database, FileKey2, RotateCcw } from "lucide-react";

export function StorageModel() {
  const [pod, setPod] = useState(1);
  const [nextPod, setNextPod] = useState(2);
  const [claim, setClaim] = useState(true);
  const [volume, setVolume] = useState(true);
  const [policy, setPolicy] = useState("Delete");
  const [message, setMessage] = useState(
    "Pod 1 reads two records through its bound claim. Remove the workload to explore the separate lifetimes.",
  );
  return (
    <section
      className="reconciliation-model"
      aria-label="Explore storage lifetimes"
    >
      <div className="section-heading">
        <div>
          <div className="eyebrow">INTERACTIVE CONCEPT MODEL</div>
          <h3>The Pod and its data have different lifetimes</h3>
        </div>
        <button
          className="icon"
          aria-label="Reset storage model"
          onClick={() => {
            setPod(1);
            setNextPod(2);
            setClaim(true);
            setVolume(true);
            setMessage("Model reset. Pod 1 reads the two original records.");
          }}
        >
          <RotateCcw size={16} />
        </button>
      </div>
      <p className="small muted">
        A simplified model, separate from your real lab. Claim protection delays
        deletion while a Pod uses it, so remove the workload first.
      </p>
      <label className="storage-policy">
        PV reclaim policy
        <select
          value={policy}
          disabled={!claim}
          onChange={(event) => setPolicy(event.target.value)}
        >
          <option value="Delete">
            Delete backing storage after claim deletion
          </option>
          <option value="Retain">Retain storage for manual recovery</option>
        </select>
      </label>
      <div className="model-pods storage-chain">
        <div className="model-pod">
          <Box size={20} />
          <strong>{pod ? `Pod ${pod}` : "No Pod"}</strong>
          <span className="small">Replaceable process</span>
        </div>
        <div className="model-pod">
          <FileKey2 size={20} />
          <strong>{claim ? "Bound claim" : "Claim deleted"}</strong>
          <span className="small">Storage request</span>
        </div>
        <div className="model-pod">
          <Database size={20} />
          <strong>{volume ? "2 stored records" : "Storage deleted"}</strong>
          <span className="small">
            {volume && !claim ? "Released volume" : "Backing volume"}
          </span>
        </div>
      </div>
      <div className="storage-actions">
        <button
          disabled={!pod}
          onClick={() => {
            setPod(0);
            setMessage(
              "The workload stopped. Its claim and both records remain.",
            );
          }}
        >
          Remove workload
        </button>
        <button
          disabled={!!pod || !claim}
          onClick={() => {
            setPod(nextPod);
            setNextPod(nextPod + 1);
            setMessage(
              `Pod ${nextPod} has a new identity and reads the same two records through the existing claim.`,
            );
          }}
        >
          Start replacement Pod
        </button>
        <button
          disabled={!!pod || !claim}
          onClick={() => {
            setClaim(false);
            setVolume(policy === "Retain");
            setMessage(
              policy === "Retain"
                ? "The claim is gone, but the released volume retains its records. An administrator must recover or reclaim it before another claim can use it."
                : "The claim is gone. With Delete, the provisioner removes the backing storage and its records.",
            );
          }}
        >
          Delete claim
        </button>
      </div>
      <div className="model-observation" role="status" aria-live="polite">
        <p>{message}</p>
      </div>
    </section>
  );
}
