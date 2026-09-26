Build a working Kubernetes 1.35.8 cluster from these two prepared Linux guests and deploy Dispatch.
Use Pod subnet `10.244.0.0/16`, authenticated discovery, the supplied native CNI, and the private host client.
Both nodes must be Ready, both CNI agents must be ready, DNS must be available, and a fresh frontend job must complete and persist.
The initialization, join-configuration, manifest-rendering, client-refresh, and application-bootstrap helpers remain available in the workspace.
Choose and carry out the sequence yourself.

Write `handoff.md` with the observations that establish each stage, the location of private credentials without copying their contents, and the single points of failure that remain.
The handoff is self-reviewed; live checks assess technical outcomes rather than claiming to interpret your prose.
