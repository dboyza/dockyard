## Your first complete operating brief

The local application is deployed, but background jobs are not completing.
The API is reachable, the database contains an original job, and the worker configuration was changed during a release.
You must diagnose the failure, deliver a precisely selected release, apply appropriate application restrictions, and prove recovery from a real logical backup.

This capstone spans the six container-engineering modules.
The supplied application source is complete; your infrastructure and operational decisions are the work being assessed.
Use direct observations to distinguish process, network, configuration, and data failures.

## Recovery has a separate target

The original job's identity is `capstone-$DOCKYARD_LAB`.
Use PostgreSQL's logical backup tools and restore into a separate database named restored in the owned database server.
This tests schema and data restoration without replacing the live application database.
It is a genuine logical restore, while later Kubernetes and VM exercises add different failure domains and recovery mechanisms.

## A handoff should be reproducible

Write RUNBOOK.md for another operator who did not watch you work.
Explain startup, verification, the diagnosed failure, backup, restore, stop/resume, and the local-to-production limitations.
The checker establishes that a runbook file exists, but its clarity and reasoning are explicitly self-reviewed.
It does not claim to grade prose quality from a filename or length.

A successful mission creates an immutable source-and-evidence checkpoint.
The checkpoint excludes runtime data archives, environment files, kubeconfigs, known lab credentials, and Kubernetes Secret documents.
Your live data stays in the practice environment; the export is an infrastructure portfolio, not a database backup.
