## Upgrade the cluster and hand it over

Upgrade the cluster from 1.36.5 to 1.37.1 in place.
Both nodes must end Ready and uncordoned, and a new job must complete.
Keep the original namespace, nodes, marker object, and stored data.

Write `maintenance-handoff.md` covering the order you followed, what you saw before and after, when the service was interrupted, what backup you would want before doing this in production, and the remaining risks.
Then compare it with `handoff-rubric.md`.
