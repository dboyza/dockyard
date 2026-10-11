## Close the access review findings

The review found:

- **Anonymous access**: callers without credentials can read objects in `dispatch`. Afterwards, requests without credentials must be refused with 401 everywhere except `/livez`, `/readyz`, and `/healthz`.
- **Long-lived tokens**: at least one Secret of type `kubernetes.io/service-account-token` exists outside `kube-system`. None may remain.
- **Auditors**: the `auditors` group can change things across the whole cluster. They need to read `dispatch` and `frontend`, including Pod logs, without Secrets, and nothing else.

Dispatch must keep processing jobs, and the original namespace, nodes, marker object, and stored data must remain.

Write `access-report.md` describing each finding, your fix, the evidence it worked, and what your changes might affect.
Then compare it with `report-rubric.md`.
