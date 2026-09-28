## Connect Dispatch to an internal dependency

Build the supplied files as `$DOCKYARD_IMAGE`.
The Dockerfile declares `ARG BASE_IMAGE`, so supply it as you did in the image lessons.
Read the end of the build output: if the build fails, an older image with the same tag can hide the mistake.
Create `$DOCKYARD_NETWORK` with the lab ownership label.
Run the API as `$DOCKYARD_CONTAINER` and its peer as `$DOCKYARD_CONTAINER-dependency`, with the same lab label on both.

Attach both to that network and give the peer the alias `dependency`.
Set the API’s upstream URL to `http://dependency:8080/healthz`.
Publish only the API, using `127.0.0.1:$DOCKYARD_PORT:8080`.
Leave both processes running.

Before checking, verify the host-to-API request, the API’s lookup of the peer, and a `/dependency` response that identifies that peer.
In your notes, explain where you would look for a host-port conflict and where you would look for a failed name lookup.
Those are different points in the request path.
