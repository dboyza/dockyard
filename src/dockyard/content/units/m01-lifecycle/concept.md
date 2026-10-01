## Stop the program, keep the container

In the last lesson you stopped Dispatch and started it again.
Now let’s look more closely at what changed and what stayed the same.

A container moves through a few states:

- **created**: Docker has saved the container’s settings, but its program has not started.
- **running**: its main process is running.
- **exited**: its main process has finished, or was stopped.

Four commands move a container between those states:

- `docker create` makes a container with its settings but does not start it.
- `docker start` starts an existing container.
- `docker stop` asks its main process to finish.
- `docker rm` removes a stopped container completely.

`docker run`, which you used in the last lesson, is simply `create` and `start` in one command.

```figure
container-states
```

Each container also has a small private area for any files its program changes, called its **writable layer**.
Stopping keeps that area; removing the container deletes it.
The image the container was made from is not affected either way.

## Names and IDs

Every container gets a long, unique **ID** when it is created.
A **name** is a friendlier label that points at one container.
Starting and stopping the same container keeps its ID.
If you remove a container and run a new one with the same name, you get a new ID: it is a different container that happens to reuse the name.
That difference matters later, when you wonder why old logs or files have disappeared.

```figure
container-identity
```

## Ask Docker what it has

`docker ps` shows only running containers.
Add `-a` to include created and exited ones too.

To see a container’s details, use `docker inspect`.
It prints a large document, so these examples pick out just the part we need:

```sh
docker inspect --format '{{.State.Status}}' "$DOCKYARD_CONTAINER"
docker inspect --format '{{.Id}}' "$DOCKYARD_CONTAINER"
docker inspect --format '{{.Config.Image}} {{json .Config.Cmd}}' "$DOCKYARD_CONTAINER"
docker inspect --format '{{json .HostConfig.PortBindings}}' "$DOCKYARD_CONTAINER"
```

The text after `--format` is a template Docker fills in; copy it exactly as shown.
The four commands show, in order, the state, the ID, the image and command, and how ports on your computer connect to ports in the container.

## Try it

In this lab, Dockyard has created Dispatch’s container but not started it.
Run the first inspect command and you should see `created`.
Then note the ID, start the container, and check it:

```sh
docker start "$DOCKYARD_CONTAINER"
docker ps --filter "name=$DOCKYARD_CONTAINER"
curl "http://127.0.0.1:$DOCKYARD_PORT/healthz"
```

If the request fails straight after starting, wait a second and try again; the application needs a moment to begin listening.

Now stop and start it once more, and print the ID again.
It should be exactly the same as before, because it is still the same container.

Settings such as port mappings and environment variables are fixed when a container is created.
Restarting keeps them.
To change one, you create a replacement container, which you will do in later lessons.

## Where the process really runs

On macOS and Windows, Docker Desktop runs your containers inside a small Linux virtual machine.
On Linux, they run directly on your computer.
Either way, use Docker commands such as `docker stop` and `docker logs` to manage a container, rather than trying to find and control its process yourself.
