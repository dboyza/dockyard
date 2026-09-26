After permission maintenance, creating jobs fails even though the service is still available.
The API still answers health checks and can read its original job, but creating new jobs fails.
Restore writes as UID 10001 while retaining the original named volume and original job.
Do not solve this by running the application as root, granting group/world write access, deleting data, or creating a replacement empty database.
