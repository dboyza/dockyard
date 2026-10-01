## Why is the old version still running?

You changed a file, rebuilt the image, and still see the old application response.
That can be correct: the file, image, and running container are three separate things.
In this lesson you’ll change one at a time and observe the difference.

Your workspace contains the files you are editing.
An image is the package produced by a build.
A container uses the image selected when that container was created.
An **image tag** is a name that can be moved to a newer image; it does not update existing containers.
Even stopping and starting an existing container keeps its original image.

```figure
file-image-container
```

## Watch the release through three changes

Prepare the lab and open its terminal.
The supplied Dockerfile already works, and a container is serving `dispatch-1`.
Read `VERSION`, then request the running release:

```sh
cat VERSION
curl --fail "http://127.0.0.1:$DOCKYARD_PORT/healthz"
```

Edit `VERSION` to contain `dispatch-2` and save it.
Before rebuilding, repeat the request.
It should still return `dispatch-1`: saving a local file did not change the image or container.

Now build the image using the same command as the previous lesson:

```sh
docker build --build-arg "BASE_IMAGE=$DOCKYARD_PYTHON_IMAGE" -t "$DOCKYARD_IMAGE" .
docker image inspect --format '{{.Id}}' "$DOCKYARD_IMAGE"
docker inspect --format '{{.Image}}' "$DOCKYARD_CONTAINER"
```

The two image IDs should differ after this change.
The tag now selects the rebuilt image, but the running container still uses the earlier one.
Repeat the health request and predict its release before reading the response.

Finally, stop and remove only this lab’s container, then create a new one from the rebuilt image:

```sh
docker stop "$DOCKYARD_CONTAINER"
docker rm "$DOCKYARD_CONTAINER"
docker run -d --name "$DOCKYARD_CONTAINER" \
  --label "io.dockyard.lab=$DOCKYARD_LAB" \
  -p "127.0.0.1:$DOCKYARD_PORT:8080" "$DOCKYARD_IMAGE"
```

The next successful health request should report `dispatch-2`.
If you send it immediately after startup, give the application a moment and try again.
We do not mount your workspace here because the point is to test the files packaged in the image.

## What the build cache saves

Docker can reuse a build step when its instruction and relevant inputs have not changed.
This reuse is the **build cache**.
When a file used by `COPY` changes, that step and later dependent steps must be rebuilt.
Changing only the file’s modification time does not count as changing its contents for this purpose.

For an application with third-party Python packages, this order can save work:

```dockerfile
COPY requirements.txt ./
RUN python -m pip install --no-cache-dir -r requirements.txt
COPY service/ ./service/
```

`requirements.txt` lists the packages, and `service/` contains the application source.
A source-only edit can reuse the earlier package-installation step.
A changed requirements file causes the installation and later steps to run again.

```figure
build-cache
```
This small Dispatch version has no third-party packages yet, so you do not need to add that example to its Dockerfile.

When the wrong release appears, compare the file, image, and container before disabling the cache.
A perfectly correct cached build cannot update a container that you have not replaced.
