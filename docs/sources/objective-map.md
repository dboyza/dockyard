# Official objective source and coverage contract

Dockyard's objective text is attributed to the Cloud Native Computing Foundation (CNCF) and reused under [CC BY 4.0+](https://creativecommons.org/licenses/by/4.0/).
The canonical machine-readable map is `src/dockyard/content/objectives.json`.
It pins CNCF curriculum repository revision `f6c7667265fef850daaf93b4e19e919552c67d8c`, the CKA and CKAD v1.35 PDF URLs, file hashes, domain weights, and the checked date of 2026-09-26.
The complete objective pages were extracted and visually inspected against the source PDFs.
Whitespace and line wrapping are normalized; the CKAD source's wording "API depreciations" is interpreted as API deprecations.

Each objective maps to explaining units, hands-on units, and independent missions.
These mappings are implementation contracts, not evidence that an unimplemented unit is complete.
A coverage report must resolve all referenced IDs against the authored catalog and real-runtime validation evidence before claiming full coverage.
At this development checkpoint only Docker Modules 1-6 are implemented and verified.

The Kubernetes implementation must explicitly include DaemonSet selection in the workload lab, ephemeral volumes in the Pod-pattern lab, removed-API diagnosis in declarative workflows, real LoadBalancer behavior, and the stated HA, CNI, CSI, CRI, operator, and Gateway objectives.
Those details must not be inferred from generic module titles.
If a focused extra exercise is needed to establish any objective, add it without reducing the approved scope.
