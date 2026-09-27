# Incident report

An egress-policy cleanup was followed by failed API requests and repeated worker dependency errors.
The trusted frontend can still connect to the API address.
Recover DNS resolution and both application dependency paths without weakening the intended network boundary.

Preserve the default-deny intent, the original namespace, the database claim, and its stored job.
A fresh job from the trusted frontend must complete and have its result persisted in PostgreSQL.
The existing denied clients and unrelated egress destination must remain blocked.
Keep the working RBAC, admission, and process settings.

Record which observation distinguished a DNS failure from a port-policy failure and why one successful connection was insufficient evidence.
The debrief is a self-review rubric for that explanation.
