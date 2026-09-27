# Diagnose the egress boundaries

A numeric-address TCP connection can work while a name lookup fails.
Treat resolution and dependency transport as separate observations.
NetworkPolicy allows traffic through the union of applicable rules, and both source egress and destination ingress can constrain a connection.
For example, an application allowed to reach a database on 5432 still cannot resolve its name if DNS egress is missing.
A rule allowing 5433 instead is not close enough: ports are exact transport endpoints.
Use the supplied clients to compare allowed traffic with denied controls instead of removing all policies to make one request succeed.

The trusted frontend must reach the API, but not PostgreSQL directly.
The untrusted frontend and the matching-label client in another namespace must remain unable to reach the API.
The API and worker need PostgreSQL and Redis, while the API must remain unable to reach the unrelated egress target.
Both UDP and TCP DNS need to work.
