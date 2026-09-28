## Build a cluster and deploy Dispatch

From the two prepared VMs, build a Kubernetes 1.35.8 cluster and deploy Dispatch:

- Pod subnet `10.244.0.0/16`;
- the worker joined with a CA-pinned configuration;
- the supplied Calico network;
- your lab terminal’s private client refreshed.

Both nodes must be Ready, Calico ready on both, DNS available, and a new job from the frontend must complete and be saved.

Write `handoff.md` listing the evidence for each stage, where the private credentials are (without copying them), and the single points of failure that remain.
