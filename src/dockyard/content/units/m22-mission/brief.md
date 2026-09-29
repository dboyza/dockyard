## Restore Dispatch across network, DNS, and storage

Diagnose and fix the worker’s forwarding setting, the trusted frontend’s DNS settings, and the database’s placement.
Then prove: a frontend request reaches an API Pod IP across nodes, a new Service name resolves and routes, the original database volume and data are in use, and a new job completes.

Do not rebuild the cluster or replace the database.
Write `infrastructure-handoff.md` covering the symptoms, what you suspected, what you observed, what you changed, and how you proved the data survived, then compare it with `handoff-rubric.md`.
