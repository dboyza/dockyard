## Two questions about what you ship

Before you send an image to someone else, it is worth checking two things:

1. Will it run on their computer’s kind of processor?
2. Does it contain anything that should have stayed private?

## Processor architecture

Container images are built for a particular kind of processor.
Apple Silicon Macs and many cloud servers use **ARM64**; most Windows PCs and older Macs use **x86-64**, which Docker calls `amd64`.
Docker combines the operating system and processor into a **platform** name, such as `linux/arm64` or `linux/amd64`.
All containers here are Linux containers, even on macOS and Windows.

An image built for a different processor may still run through emulation, but slowly and sometimes incorrectly.
Dockyard sets `DOCKER_DEFAULT_PLATFORM` in your lab terminal to your computer’s own platform.
Check what an image was built for rather than guessing from its name:

```sh
echo "$DOCKER_DEFAULT_PLATFORM"
docker image inspect --format '{{.Os}}/{{.Architecture}}' "$DOCKYARD_IMAGE"
```

Many public images are published for several platforms under one name, and Docker automatically downloads the one that matches your computer.

```figure
image-platforms
```

## Secrets in images

This lab’s Dockerfile uses `COPY . .`, which copies everything in the build folder into the image.
The folder contains a file called `.env`, a common place for passwords.
Here it is a harmless fake, but in real projects this is a classic way to leak secrets.

Remember that an image is a stack of layers.
If one step copies `.env` in and a later step deletes it, the file is hidden from the running container but still stored in the earlier layer.
Anyone who has the image can extract it.

```figure
secret-in-layers
```

The fix is to stop the file entering the build at all.
Either copy only the files the app needs, or list the file in a `.dockerignore` file next to the Dockerfile:

```dockerignore
.env
*.key
.git
__pycache__
```

Each line is a pattern for files the build should never see.
Leave the fake `.env` in your workspace; the point is that the build ignores it.

## Build for your platform and check

```sh
docker build --platform "$DOCKER_DEFAULT_PLATFORM" --build-arg "BASE_IMAGE=$DOCKYARD_PYTHON_IMAGE" -t "$DOCKYARD_IMAGE" .
```

`--platform` states the target platform explicitly.
Then replace the running container so it uses the new image.
Check work examines every layer of the running image for `.env`, so deleting it in a later step will not pass.

## What this does not prove

Knowing an image’s platform and inputs is useful, but it does not tell you whether the software inside has known security problems or who built it.
Later, the security modules cover scanning images and recording what they contain.
