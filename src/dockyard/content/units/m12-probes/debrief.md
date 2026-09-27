# Debrief: Separate startup, readiness, and liveness

Startup, readiness, and liveness answer different questions and trigger different controller behavior.
The real endpoint observations and clean SIGTERM exit connect those policies to the supplied process rather than just to fields in a manifest.

## Explain your result

Why can a dependency outage justify withholding traffic while restarting the process repeatedly makes the outage harder to recover from?

## Transfer beyond this lab

Choose probe thresholds from measured startup and failure behavior instead of copying the local lab timings into production.
