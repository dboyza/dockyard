## A tag is a useful name, not an immutable identity

A tag such as dispatch:release can move to new content.
An existing container retains its selected image even after that tag moves.
A registry digest identifies a particular manifest by its content hash, giving a deployment a precise artifact reference.
A local image ID and a registry manifest digest describe related but different objects; do not assume their hash strings must match.

A registry stores and distributes image manifests and layers.
This lab provides an owned registry bound to a separate assigned loopback port, with its data in a labeled volume.
It does not change Docker Desktop's global daemon configuration or publish a service to other machines.
Its unauthenticated local HTTP setup is for this isolated practice environment, not a production registry security design.

## Worked example: add a distribution name

```sh
registry="127.0.0.1:$DOCKYARD_REGISTRY_PORT"
docker tag "$DOCKYARD_IMAGE" "$registry/dispatch:candidate"
docker push "$registry/dispatch:candidate"
```

Tagging adds a reference to the existing artifact; it does not rebuild the application.
Pushing transfers missing content and reports the registry digest.
A deployment reference of the form `registry/dispatch@sha256:...` selects that exact manifest instead of asking a mutable tag what it means later.

## Inspect all three identities

Use docker image inspect to compare the local Id and RepoDigests entries.
Use docker inspect on a running container to see its Config.Image selection and actual Image ID.
A repository can contain several tags for the same content, and one local image can accumulate references from several registries.
Choose the digest associated with this lab's registry, not an arbitrary first entry from an unrelated previous push.

## Distribution still needs behavioral verification

A successful push establishes that the registry accepted content.
It does not prove the image runs, listens on the expected port, or contains the intended release.
The checker verifies both the exact manifest served by the registry and a live response from the application selected by that digest.
