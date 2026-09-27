# Debrief: Diagnose an unavailable API from the host

Host-side inspection remains available when kubectl cannot reach a working API.
Recovering the endpoint requires the kubelet and static control-plane processes to function together, followed by a fresh scheduling and application check.

## Explain your result

Which evidence distinguished a broken API dependency from a kubeconfig or transport problem, and why was repeatedly retrying kubectl insufficient?

## Transfer beyond this lab

Keep a bounded host-recovery procedure and independently protected access for outages where API-level automation cannot operate.
