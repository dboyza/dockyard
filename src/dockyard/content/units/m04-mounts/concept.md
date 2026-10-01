## Keep jobs when you replace the container

Dispatch now stores jobs in a small SQLite database: one file at `/data/jobs.db`.
You do not need to write SQL for this lesson.
You will submit a job, replace its container, and check that the job is still there.

A container normally writes changes into its own writable layer.
Removing that container removes those changes.
A **mount** gives a path inside the container access to storage that exists separately.
Here, mount `/data` so the database survives; leave `/app` alone so the packaged application stays visible.

There are two useful choices:

- A **bind mount** uses a directory you choose on your computer.
- A **named volume** uses storage managed by Docker.

Both can survive container replacement.
Neither protects you from deleting or corrupting the data itself, so neither replaces a backup.

```figure
storage-choices
```

## Build and start the storage version

Prepare the lab and open its terminal.
The supplied Dockerfile and Python application are complete.
Build them, create the host directory, then start the API:

```sh
docker build --build-arg BASE_IMAGE="$DOCKYARD_PYTHON_IMAGE" -t "$DOCKYARD_IMAGE" .
mkdir -p "$DOCKYARD_STORAGE"
docker run -d --name "$DOCKYARD_CONTAINER" \
  --label "io.dockyard.lab=$DOCKYARD_LAB" \
  --user "$(id -u):$(id -g)" \
  --mount "type=bind,source=$DOCKYARD_STORAGE,target=/data" \
  -p "127.0.0.1:$DOCKYARD_PORT:8080" "$DOCKYARD_IMAGE"
```

`id -u` and `id -g` return your user and group numbers in the lab terminal.
Using them for this container lets it write to the directory you just created.
On Windows, these are your WSL user’s numbers.
The next lesson uses a Docker-managed volume and a different ownership arrangement.

The `--mount` option names the storage type, source, and destination explicitly.
It reports an error if the source directory is missing.
Mounting over `/app` instead would hide the application files you built into the image.

## Write a job, then replace its container

Once the server has started:

```sh
curl --fail -H 'Content-Type: application/json' \
  -d '{"title":"keep this job"}' "http://127.0.0.1:$DOCKYARD_PORT/jobs"
curl --fail "http://127.0.0.1:$DOCKYARD_PORT/jobs"
```

The `-d` option sends a request body and makes this a POST request.
The header tells the API that the body is JSON.
Record the returned job’s identity.
Stop and remove only the assigned container, then repeat the same `docker run` command, including its mount.
Request `/jobs` again: the same job should still be present.

```figure
replace-with-mount
```

The checker also creates its own temporary job and reads the committed database through the mount independently.
It removes that observation afterward and leaves your jobs intact.
It checks the current storage arrangement; your before-and-after observation is what demonstrates replacement to you.
