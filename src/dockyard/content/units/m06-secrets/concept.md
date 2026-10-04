## When the build itself needs a secret

The previous lesson kept a private file out of the image by keeping it out of the build.
Sometimes that is not enough, because a build step genuinely needs a secret: a token to download from a private package server, or a key to sign the release.
The step must be able to read the secret, yet nothing it leaves behind may contain it.

In this lab, Dispatch's release is **signed** during the build.
`sign.py` reads a release token from its standard input and writes a signature for the `VERSION` file into `SIGNATURE`.
Anyone holding the same token can check that signature later, so the token itself must stay private.

## Why a build argument leaks

A **build argument** passes a value into the build with `--build-arg NAME=value` and an `ARG NAME` line in the Dockerfile.
It looks convenient, and the supplied `release.sh` uses one:

```dockerfile
ARG RELEASE_TOKEN
RUN echo "$RELEASE_TOKEN" | python sign.py > SIGNATURE
```

Docker records how each layer was made in the image's **history**, and a `RUN` step that uses a build argument records the argument's value with it.
See it for yourself:

```sh
docker image history --no-trunc --format '{{.CreatedBy}}' "$DOCKYARD_IMAGE"
```

Two lines show the token: `ARG RELEASE_TOKEN=dyk_practice_...` and `RUN |1 RELEASE_TOKEN=dyk_practice_... /bin/sh -c ...`.
The history travels with the image, so anyone you give it to can read the token.
BuildKit, the engine behind `docker build`, even prints a `SecretsUsedInArgOrEnv` warning for this pattern.
`ENV` is worse still: its value is also stored in the image's configuration and set in every container.

```figure
build-secret
```

## Secret mounts

BuildKit has a safer channel built for exactly this, the **build secret**.
You hand the secret to the build command, and one `RUN` step mounts it as a file:

```dockerfile
RUN --mount=type=secret,id=release_token,required=true python sign.py < /run/secrets/release_token > SIGNATURE
```

```sh
docker build --secret id=release_token,src=release-token.txt ...
```

- `--secret id=release_token,src=release-token.txt` makes the workspace file available to the build under the name `release_token`.
- `--mount=type=secret,id=release_token` mounts it at `/run/secrets/release_token`, for this one step only.
- `required=true` makes the step fail if the build command did not supply the secret, instead of quietly running without it.

The file exists only while that step runs.
It is not written into the layer, and the history records the command, not the secret's contents.
If a tool expects an environment variable instead, `--mount=type=secret,id=release_token,env=RELEASE_TOKEN` sets one for that step only.

One thing to watch: the secret is not part of the build cache's key.
If only the secret changes, Docker may reuse the cached step and keep the old result; rebuild with `--no-cache` after changing it.

## See the leak

Prepare the lab, then run the history command above and find the token.
`release-token.txt` holds a harmless practice value, so seeing it printed is safe here.

## Fix it

1. In the `Dockerfile`, remove the `ARG RELEASE_TOKEN` line and change the signing step to read the token from a secret mount.
2. In `release.sh`, replace the `RELEASE_TOKEN` build argument with `--secret id=release_token,src=release-token.txt`.
3. Run `sh release.sh`, then replace the running container with one from the new image:

```sh
docker rm -f "$DOCKYARD_CONTAINER"
docker run -d --name "$DOCKYARD_CONTAINER" --label "io.dockyard.lab=$DOCKYARD_LAB" -p "127.0.0.1:$DOCKYARD_PORT:8080" "$DOCKYARD_IMAGE"
```

Run the history command again; the token should be gone, and `docker exec "$DOCKYARD_CONTAINER" cat SIGNATURE` should still show a signature.

## If something goes wrong

- **The build fails with a missing secret**: `required=true` is doing its job. Check that the `id` in `--secret` matches the `id` in `--mount`.
- **The signature step fails with no token**: the secret mount is there, but `sign.py` is not reading it. Redirect `/run/secrets/release_token` into its standard input with `<`.
- **The token is still in the history**: the old image is still running. Rebuild, then replace the container.
