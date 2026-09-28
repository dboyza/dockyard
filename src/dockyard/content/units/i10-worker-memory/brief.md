## Get the workers finishing jobs again

- Run two stable workers that keep their 80 MiB working set and finish new jobs.
- Give each worker a memory limit between 128 and 256 MiB, with a request no larger than the limit.
- Keep the application code, the database’s storage, and the original job.
- Do not remove the limit or delete the workload.

In your notes, record the first observation that pointed at the cause, your fix, and a check you could run to catch this after future budget changes.
