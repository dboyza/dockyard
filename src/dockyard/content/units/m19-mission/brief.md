Restore the existing native environment so that:

- The worker's ordinary `sudo crictl info` reaches the runtime and its running API process belongs to the expected systemd cgroup hierarchy.
- Both kubelet services are active, both nodes are Ready, and their leases are fresh.
- The separate guest operator client lists both nodes using valid trust and private file permissions.
- The four kubeadm static components remain running and a fresh Dispatch job completes through the frontend and persistent database.

Preserve the current guests, application workloads, and database claim.
Use the observations from previous lessons to choose your own repair sequence.
Write a short handoff in `handoff.md` explaining each failed boundary, the evidence supporting its repair, and one observation that would falsify your conclusion.
The handoff uses self-review; automatic completion grades the live technical criteria rather than claiming to understand your prose.
