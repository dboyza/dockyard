## From a mounted directory to an artifact

The first module mounted app.py from your host computer into a reusable Python image.
That is convenient for experimentation, but another machine would also need your source directory.
An application image carries the files and runtime configuration required to start the service.
Building the image and running a container are separate operations.

A Dockerfile is a build recipe.
`FROM` selects a base image, `WORKDIR` sets the working directory, and `COPY` adds files from the build context.
`RUN` executes during the build and commits its filesystem changes into the next layer.
`CMD` records the default command for a future container; it does not start the application during the build.

## The context is a boundary

In `docker build -t my-image .`, the final dot names the current directory as the build context.
A COPY instruction reads from that context, not from arbitrary paths on the host.
A `.dockerignore` file excludes files before they become available to the build.
Exclude private credentials, local caches, and irrelevant large directories.
An excluded file cannot be copied merely because it exists beside the Dockerfile.

## Worked example: package a one-shot tool

```dockerfile
ARG BASE_IMAGE
FROM ${BASE_IMAGE}
WORKDIR /tool
COPY report.py ./
CMD ["python", "report.py"]
```

This recipe runs a supplied report script when a container starts.
For an HTTP application, the main command must remain running and listen on the correct address.
The task below packages an API rather than a one-shot report.

```sh
docker build --build-arg "BASE_IMAGE=$DOCKYARD_PYTHON_IMAGE" -t "$DOCKYARD_IMAGE" .
docker image inspect "$DOCKYARD_IMAGE"
```

Dockyard supplies a digest-pinned Python base through the environment.
The resulting local application tag is a convenient reference for this lab's builds.
Later you will distinguish that mutable tag from an immutable digest.

## Ports are still runtime choices

`EXPOSE 8080` documents an intended container port.
It does not publish that port on your host computer.
The container run command still needs a loopback-bound `-p` mapping.
The application must listen on `0.0.0.0` inside the container to accept forwarded requests.
