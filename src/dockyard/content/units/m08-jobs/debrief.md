# Debrief: Run finite and scheduled maintenance

A CronJob describes scheduling policy, whereas a Job records one finite execution and its completion behavior.
The proof Job performs a real database observation, so a valid cron expression alone cannot satisfy the task.

## Explain your result

Explain what concurrency and retry policy protect against, and what one successful proof run cannot tell you about a month of scheduled executions.

## Transfer beyond this lab

Production maintenance also needs idempotent operations, time-zone awareness, alerting, and a plan for missed schedules.
