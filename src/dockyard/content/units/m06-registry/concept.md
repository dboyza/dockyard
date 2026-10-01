## Share an image through a registry

So far your images have lived only on your own computer.
A **registry** is a server that stores images so other computers can download them.
Docker Hub is a public registry; companies usually run private ones.
Uploading an image is called **pushing** it, and downloading is **pulling**.

This lab runs a small practice registry for you, on its own port at `127.0.0.1:$DOCKYARD_REGISTRY_PORT`.
It is reachable only from your computer and uses no password, which is fine for practice but not for real use.

## Tags can move; digests cannot

An image name has three parts: where it lives, what it is called, and which version.
In `127.0.0.1:49804/dispatch:release`, the registry is `127.0.0.1:49804`, the repository is `dispatch`, and the tag is `release`.

```figure
image-reference
```

A **tag** is a label someone can move to a different image at any time.
If you deploy `dispatch:release` today and someone pushes a new build under the same tag tomorrow, the same name now means different content.

A **digest** is a fingerprint calculated from the image’s content, written like `sha256:3f1a...`.
If the content changes, the digest changes.
Deploying `dispatch@sha256:3f1a...` always gets exactly the same image, which is why careful teams deploy by digest.

```figure
tags-vs-digests
```

## Push an image

```sh
registry="127.0.0.1:$DOCKYARD_REGISTRY_PORT"
docker tag "$DOCKYARD_IMAGE" "$registry/dispatch:release"
docker push "$registry/dispatch:release"
```

The first line saves the registry address in a shell variable to keep the commands short.
`docker tag` gives your existing image an extra name that includes the registry; it does not copy or rebuild anything.
`docker push` uploads it and, at the end, prints a line containing `digest: sha256:...`.

## Find the digest and run by it

Docker also records the digest on the image after a push:

```sh
docker image inspect --format '{{json .RepoDigests}}' "$registry/dispatch:release"
```

The output is a list of names like `127.0.0.1:49804/dispatch@sha256:...`.
If you have pushed to other registries before, the list can hold several; pick the one that starts with this lab’s registry address.

Pull that exact reference, then run the container from it with the usual name, label, and port mapping:

```sh
docker pull "127.0.0.1:$DOCKYARD_REGISTRY_PORT/dispatch@sha256:<the digest you found>"
```

Replace `<the digest you found>` with the long value from the previous command.
Afterwards, `docker inspect --format '{{.Config.Image}}' "$DOCKYARD_CONTAINER"` shows the reference the container was created from; it should contain `@sha256:`.

You may notice the image ID from `docker image ls` is a different long number from the digest.
They are calculated from different data, so they are not expected to match.

## A successful push is not a working release

A push only shows the registry accepted the upload.
You still need to run the image and make a request to know it works.
