## Prove a clean stop

Prepare starts a healthy Dispatch instance for this exercise.

1. Make a successful request to `/healthz` and locate its HTTP 200 request line in the container's logs.
2. Stop the assigned container using normal graceful termination.
3. Inspect its final state and exit code.
4. Leave the container present but stopped, then check your work.

Use `docker stop` in the terminal for this task.
Dockyard's separate Stop button pauses a practice environment and therefore blocks assessment until resumed.
Do not delete the container: its state and logs are the evidence this exercise needs.
