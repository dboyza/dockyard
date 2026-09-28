## Maintenance without losing capacity

Relaxing the budget to one allowed exactly one eviction at a time, the Deployment replaced the evicted copy on the other worker, and the database never moved.

Check your understanding:
Why did the drain wait forever while the budget required both copies?
What would stop the replacement Pod from starting if the API used *required* anti-affinity?
