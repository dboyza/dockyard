## Get jobs finishing again

Find out why the workers are not completing jobs, then fix the cause.

- Keep the existing PostgreSQL volume and its data.
- Keep the database and queue private, and the API on `127.0.0.1:$DOCKYARD_PORT`.
- Run two workers.
- Submit a new job and confirm a worker finishes it and its result is saved.

In your notes, record the symptom, the evidence that pointed to the cause, your fix, and how you confirmed it.
Explain why resetting the database would have been the wrong move.
