# Restore the credential delivery path

PostgreSQL is initialized with the lab's generated practice password.
The API Secret volume references a key that does not exist, so the Pod cannot mount the expected password file.

Repair the `database-credential` volume in `platform.yaml` so the `password` key becomes `/var/run/dispatch/password`.
Keep the volume read-only and keep `DB_PASSWORD_FILE` pointing at that file.
Do not replace the reference with a literal password in the Pod environment or source code.
Apply and wait for the API to become available, then verify `/readyz` and a real job round trip.
The checker compares the delivered value internally without displaying it in evidence.
