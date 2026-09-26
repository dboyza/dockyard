## Three versions can coexist

Your workspace, an image tag, and a running container can each refer to different application content.
Editing a file changes only the workspace.
Building a new image can move a tag to a new image ID.
An existing container still uses the image selected when that container was created.
Restarting it does not replace that image with whatever its tag points to now.

## Cache reuse follows inputs

Docker can reuse a previous build result when the instruction and relevant inputs have not changed.
A changed COPY input invalidates that step and dependent later steps.
File modification time alone does not serve as the decisive content change signal for COPY.
Avoid the habit of disabling the cache whenever results are confusing; first establish which artifact is stale.

A typical dependency-heavy application copies its dependency manifest before rapidly changing source.
It installs dependencies in that earlier layer so a source-only change can reuse the expensive installation result.
This small checkpoint has no third-party dependencies, so there is no installation layer to optimize yet.

## Worked example: keep an expensive step reusable

```dockerfile
COPY requirements.txt ./
RUN python -m pip install --no-cache-dir -r requirements.txt
COPY service/ ./service/
```

Changing service code invalidates the final copy without necessarily reinstalling the same dependencies.
Changing requirements invalidates the installation and later layers.
Do not put private credentials in a build argument or copied file to make that installation work; later supply-chain labs cover secret handling.

## Observe identities, not just tags

```sh
docker image inspect --format '{{.Id}}' "$DOCKYARD_IMAGE"
docker inspect --format '{{.Image}}' "$DOCKYARD_CONTAINER"
docker history "$DOCKYARD_IMAGE"
```

The first two observations answer whether the running instance came from the image currently selected by the tag.
A tag is a pointer; the image ID records a particular local artifact.
`docker history` helps explain layers but does not substitute for an application response.

## Deliberate failure exercise

After editing VERSION, make a request before rebuilding.
Then rebuild and make another request before replacing the container.
Explain why those two requests can still return the old release.
Only a newly created container from the rebuilt artifact should serve the new version.
