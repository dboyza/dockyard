# Security baseline report

## Findings and fixes

- CIS 4.2.4 on the worker: the kubelet served its unauthenticated read-only API on port 10255. Set `readOnlyPort: 0` and restarted the kubelet; the live configuration now reports 0.
- CIS 1.3.2 on the control plane: the controller manager ran with profiling on. Added `--profiling=false` to its static Pod manifest; the kubelet restarted it.
- Frontend egress: the existing policy blocked only `169.254.169.254`, so frontend Pods could still reach both kubelets on ports 10250 and 10255. Replaced it with an allowlist for CoreDNS and the Dispatch API.
- Staged binaries: `kubeadm` failed its SHA-512 check and was deleted; `kubelet` and `kubectl` matched and were kept.

## Evidence

- kube-bench now passes 4.2.4 and 1.3.2.
- Both frontend clients time out connecting to the metadata address and to ports 10250 and 10255 on both nodes, while the trusted client still submits jobs.
- `sha512sum -c` reports OK for every remaining staged binary.

## Remaining risks

- Other benchmark findings, such as audit logging, are deliberately left for later work and should be reviewed.
- kube-bench used the CIS 1.12 benchmark, written for older Kubernetes versions.
