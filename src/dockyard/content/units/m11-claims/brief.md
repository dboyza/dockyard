# Mount the claim the application actually needs

The supplied claim `dispatch-data` exists, but the database Deployment still uses emptyDir.
Inspect its events and explain why the claim may remain Pending before it has a consumer.

Edit `platform.yaml` so volume `data` references claim `dispatch-data` and the database uses a Recreate update strategy.
Keep the existing mount at `/var/lib/postgresql/data` and the single database replica.
Apply `claim.yaml`, render and apply `platform.yaml`, and wait for database readiness.
Then run `python storage-proof.py` and verify that a new database Pod reads the original marker.

This starter contains no business data to migrate.
In a real migration, take and verify a backup before changing the storage destination.
Do not conclude that attaching an empty persistent volume transfers the old container's data.
