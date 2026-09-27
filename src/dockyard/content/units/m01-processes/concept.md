You already know how to start a program in a terminal.
Docker gives that program a controlled view of its filesystem, network, and operating-system resources.
A **container** is an instance of that environment with a main process and, sometimes, additional processes.
It is not a tiny computer that stays alive independently of its programs.

An **image** supplies the initial filesystem and default launch settings.
It is reusable: several containers can start from the same image while keeping separate writable layers.
The Docker daemon manages those containers; the `docker` command sends requests to that daemon.
On macOS and Windows, Linux containers share the kernel of Docker's Linux environment.
On native Linux, they share the Docker Engine host's kernel.

## Follow one request

Dispatch begins as a small HTTP API.
The supplied `app.py` responds to health and welcome requests.
We supply the application code so you can concentrate on running it correctly.
Later you will build its image, add durable storage and a worker, and operate the same system on Kubernetes.

For now, there are two distinct port numbers:

- **8080 inside the container** is the port where the Python process listens.
- **The assigned host port** is where your browser or terminal connects on the host computer.

Port publication connects those two sides.
The host port does not need to match the container port.
Binding it to `127.0.0.1` makes it reachable from this host computer rather than publishing it on every host interface.

## Run the supplied API

Prepare the lab and open its WezTerm tab.
Dockyard sets a few variables so the resources stay specific to this exercise:

- `DOCKYARD_CONTAINER` is the name reserved for your container.
- `DOCKYARD_LAB` is the label value used to identify its owner.
- `DOCKYARD_WORKSPACE` points to your real source directory.
- `DOCKYARD_PORT` is the allocated loopback port.
- `DOCKYARD_PYTHON_IMAGE` identifies the verified Python image prepared for this lab.

Inspect the source first with `cat app.py`.
Then run:

```sh
docker run -d \
  --name "$DOCKYARD_CONTAINER" \
  --label "io.dockyard.lab=$DOCKYARD_LAB" \
  -p "127.0.0.1:$DOCKYARD_PORT:8080" \
  -v "$DOCKYARD_WORKSPACE:/app:ro" \
  -w /app \
  "$DOCKYARD_PYTHON_IMAGE" python app.py
```

`-d` detaches the Docker client after startup; it does not turn a short-lived application into a long-running service.
The `--name` and `--label` options identify this particular container.
`-p` publishes the port, and `-v` mounts your source into `/app` read-only.
The `-w` option makes `/app` the working directory.
The image name is followed by the command that becomes the container's main process: `python app.py`.

The final command matters.
If you ran a Python expression that immediately exited instead, Docker would start the container and then show it as stopped.
An exit code of zero would mean the process finished successfully, not that a web service is available.

## Inspect reality

```sh
docker ps
docker logs "$DOCKYARD_CONTAINER"
curl "http://127.0.0.1:$DOCKYARD_PORT/healthz"
```

`docker ps` shows running containers.
Use `docker ps -a` when you need to see stopped containers as well.
Logs tell you what the process wrote; an actual HTTP response tells you whether a request reached the service.
Both observations are useful, and neither should be replaced with guessing from a container name.

Stop and restart the assigned container:

```sh
docker stop "$DOCKYARD_CONTAINER"
docker start "$DOCKYARD_CONTAINER"
```

While it is stopped, the health request should fail.
After it starts again, the request should succeed.
The image is available throughout, and the existing container keeps its identity across stop/start.
Removing the container is a different operation; you will investigate that lifecycle in the next lab.

## If it fails

An immediate exit usually points to the main process or its input files.
A name conflict means a container with the chosen name already exists, often from your earlier attempt.
A running container with a failed HTTP request suggests the listening address, port mapping, or application readiness needs investigation.
Read the relevant error and inspect only this lab's resource before deciding what to change.
Never use a global prune command as a substitute for understanding the failure.
