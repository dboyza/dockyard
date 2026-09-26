## Output is a stream, status is a fact

A detached container still writes standard output and standard error.
Docker's logging driver collects those streams; `docker logs` reads the captured output.
A message saying "listening" records an earlier event, so it cannot prove the service is still available now.
Combine logs with process inspection and a current request.

```sh
docker logs --tail 20 --timestamps "$DOCKYARD_CONTAINER"
docker inspect --format '{{json .State}}' "$DOCKYARD_CONTAINER"
```

`--tail` bounds a diagnostic read.
`--follow` stays attached to new output; press Control-C to leave the log viewer without stopping the application.
The viewer and the container process are different processes.

## Termination has a protocol

A normal `docker stop` sends the configured stop signal, usually SIGTERM, to the container's main process.
Docker waits for its grace period before forcefully killing an unresponsive process.
SIGTERM gives an application a chance to close listeners and flush buffered data.
SIGKILL cannot be caught and cannot provide that cleanup opportunity.

Dispatch installs a SIGTERM handler and exits with code zero.
That exit reports successful shutdown, not continuous service availability.
A one-shot migration job can also finish successfully, while an API that exits immediately is unavailable even with exit code zero.

## Worked example: correlate a request with output

```sh
curl --fail "http://127.0.0.1:$DOCKYARD_PORT/healthz"
docker logs --tail 10 "$DOCKYARD_CONTAINER"
```

Find the GET request line and its HTTP status.
An application may write startup output to stdout and request diagnostics to stderr; Docker captures both.
When redirecting logs in your shell, use `2>&1` if you intend to capture both streams.

## PID 1 and process wrappers

In a Linux container's PID namespace, the main process is PID 1.
Signal forwarding matters when a shell wrapper launches the real server as a child.
An exec-form command such as `CMD ["python", "app.py"]` avoids an unnecessary shell layer.
A deliberately written wrapper should replace itself with the server using `exec` or forward signals correctly.
The next module applies this to Dockerfiles.
