Join the worker, install the supplied native network, and deploy Dispatch with `sh bootstrap.sh`.
Both recorded nodes must be Ready, CNI agents must be ready on both nodes, and CoreDNS must be available.
A fresh cross-node frontend request must produce a completed, persisted job.

Use the CA-pinned join configuration and inspect the CNI manifest before applying it.
The practice image and pinned dependencies have already been transferred to the guests.
Explain which observations establish registration, network readiness, DNS resolution, and actual application traffic.
