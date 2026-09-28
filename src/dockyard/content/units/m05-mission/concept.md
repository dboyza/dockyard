## Bring the application up as a complete project

You have practised each part separately: describing services, waiting for dependencies, and running multiple workers.
Now build a Compose file that combines them without a prepared working stack.
The supplied Python application and Dockerfile are complete.

Plan the path of a job: the API accepts it, PostgreSQL stores it, Redis signals work, and a worker saves its completed result.
Keep the database and queue reachable inside the application network without publishing them to your computer.

Use the checks you have learned at each point in that path.
A list of running containers is a starting observation; the completed job is the result the user needs.
