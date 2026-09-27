# Incident report

A memory-budget edit coincides with worker restarts. The API still accepts jobs, but completed results stop arriving.

Restore two stable workers that retain the supplied 80 MiB working set and process fresh jobs.
Choose a per-worker memory limit between 128 and 256 MiB, with a request no greater than that limit.
Keep the application logic, database claim, and original job.
The check observes actual resident memory, restart stability, and a result read directly from PostgreSQL.
Removing the limit or deleting the workload does not meet the operational budget.

Write a short account of the first discriminating observation, the repair, and a regression check.
Use the debrief as a self-review rubric; prose is not automatically graded.
