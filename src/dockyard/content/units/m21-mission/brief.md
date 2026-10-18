## Upgrade the cluster and hand it over

Upgrade the cluster from 1.36.5 to 1.37.1 in place.
Both nodes must end Ready and uncordoned, and a new job must complete.
Keep the original namespace, nodes, marker object, and stored data.

Write `maintenance-handoff.md`.
Cover the order you followed, what you saw before and after, and when the service was interrupted.
Say what backup you would want before doing this in production, and list the remaining risks.
Then compare it with `handoff-rubric.md`.
