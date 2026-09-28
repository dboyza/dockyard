## Let Dispatch save jobs again

Find out why saving new jobs fails while reading still works, then fix the cause.

- Keep the original named volume and the original job.
- Keep the API running as user 10001.
- Do not run the API as root, give group or everyone write access, or replace the database with a new empty one.
- Confirm that a new job saves and the original job is still listed.

In your notes, record the symptom, the evidence that pointed to the cause, your fix, and how you confirmed it.
