## Restore DNS and the dependency paths

Recover name lookups and both application dependency paths without weakening the network boundary.

- Keep the default-deny policy, the namespace, the database’s storage, and its stored job.
- Keep the working RBAC, admission, and process settings.
- The clients and outside target that are blocked now must stay blocked.
- A new job from the trusted frontend must complete and be saved in PostgreSQL.

In your notes, record which observation told a DNS problem apart from a port problem, and why one successful connection was not enough evidence.
