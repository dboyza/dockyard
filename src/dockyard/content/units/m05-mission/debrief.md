## Explain the project to someone else

Your Compose file now describes both what runs and how its parts connect.
The live check follows a job through that arrangement.

Use your startup notes to explain which command preserves the existing containers, which recreates them, and which would also delete the named volume.
Then describe how you would tell a worker failure from a database readiness failure using the logs and job state.
