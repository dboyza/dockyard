The API and its readiness check work, and newly submitted jobs appear in the queue, but background results never finish.
A worker-specific configuration overlay was deployed immediately before the symptom; the API, queue, and database processes stayed healthy.
Restore two interchangeable workers while preserving the current PostgreSQL volume, private dependency network, and API endpoint.
Prove a new job completes through a real worker and persists in the database.
