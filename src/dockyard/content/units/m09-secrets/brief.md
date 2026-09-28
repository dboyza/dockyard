## Deliver the database password to the API

PostgreSQL uses this lab’s generated practice password, stored in the `dispatch-database` Secret under the key `password`.
The API’s Secret volume asks for a key that does not exist, so its Pods cannot start.

1. Find the problem from the Pod’s events, without printing the password.
2. Fix the `database-credential` volume in `platform.yaml` so the `password` key appears as `/var/run/dispatch/password`.
3. Keep the volume read-only and leave `DB_PASSWORD_FILE` as it is. Do not put the password directly in the Deployment or code.
4. Run `sh run.sh`, wait for the API, and check it is ready and can process a job.
5. Choose **Check work**.

Check work compares the delivered password internally and never displays it.
