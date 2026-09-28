## Add a worker and inspect real work

Scale the supplied worker service to at least two running replicas.
Keep the database and queue private and leave the API available on its assigned local port.
Submit several jobs and inspect their completed results and worker identities.

Run the optional `inspect` service through the `tools` profile and observe its database name lookup.
Then follow the lesson’s guided PostgreSQL backup and separate restore exercise.
Find one of your completed jobs in the restored database.

The checker verifies replicas and background processing.
Review the diagnostic output and backup exercise yourself; the later capstone checks restoration directly.
