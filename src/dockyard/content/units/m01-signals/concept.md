## What can the logs tell you?

A program running in a container still prints messages, even though you cannot see its screen.
Programs have two output channels: **standard output** for ordinary messages and **standard error** for errors and warnings.
Docker collects both, and `docker logs` shows them to you.

```figure
log-streams
```

```sh
docker logs --tail 20 --timestamps "$DOCKYARD_CONTAINER"
```

`--tail 20` shows only the last 20 lines, and `--timestamps` adds the time each line was written.
Adding `--follow` keeps showing new lines as they arrive.
Press Control-C to leave it; that stops the log viewer in your terminal, not Dispatch.

Remember that logs describe the past.
A line saying Dispatch is "listening" tells you it started; it does not prove it is still answering now.
To know that, make a fresh request.

## Match a request to its log line

```sh
curl --fail "http://127.0.0.1:$DOCKYARD_PORT/healthz"
docker logs --tail 5 "$DOCKYARD_CONTAINER"
```

`--fail` makes curl report an error if the server returns an error status.
In the logs, look for a line containing `GET /healthz` followed by `200`.
**200** is the HTTP status code for a successful request.

## How a container stops

When you run `docker stop`, Docker sends the main process a **signal**, a short message from the operating system.
The usual one is **SIGTERM**, which means “please finish up and exit.”
A well-written program catches it, closes its connections, and exits.
If the program ignores it, Docker waits about ten seconds and then sends **SIGKILL**, which ends the process immediately with no chance to clean up.

When a process ends it reports an **exit code**.
Zero means it finished normally; any other number means something went wrong.
Dispatch handles SIGTERM and exits with code 0, so a normal `docker stop` should leave it `Exited (0)`.
A process killed with SIGKILL usually shows `Exited (137)`.

```figure
stop-signals
```

Be careful what you conclude from exit code 0.
It means the program finished without an error.
For a one-off task, such as a database migration, finishing is the goal.
For a web service like Dispatch, finishing means it is no longer answering requests, even though nothing “failed.”

## See it for yourself

After stopping the container, read its final state:

```sh
docker ps -a --filter "name=$DOCKYARD_CONTAINER"
docker inspect --format '{{.State.Running}} {{.State.ExitCode}}' "$DOCKYARD_CONTAINER"
docker logs --tail 5 "$DOCKYARD_CONTAINER"
```

The logs are still there after the container stops.
They disappear only when the container is removed.

## Looking ahead

Inside a container, the main process has process number 1, and it is the one that receives Docker’s stop signal.
If a shell script starts the real server as a background task and then finishes, the container stops with it, even though the server had started.
You will meet this problem again when you write Dockerfiles.
