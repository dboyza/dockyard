## Ship the source change

Prepare supplies a working Dockerfile and starts release `dispatch-1` from an image.
Change VERSION to `dispatch-2`.
Build the updated image under the assigned tag, then replace only the assigned container with a new instance of that image.
Keep the required lab label and loopback port mapping.
Do not bind-mount local source as a shortcut.

Leave `/healthz` serving release `dispatch-2`.
Use the intermediate requests described above to distinguish a changed file, a rebuilt image, and a replaced running instance.
