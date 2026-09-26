## Package Dispatch

The checkpoint supplies app.py and VERSION; they are ready to use.
Write a Dockerfile that accepts `BASE_IMAGE`, copies both files into `/app`, and runs `python app.py` there as its foreground command.

Build the result as `$DOCKYARD_IMAGE` using the pinned `$DOCKYARD_PYTHON_IMAGE` build argument.
Start it under `$DOCKYARD_CONTAINER`, attach label `io.dockyard.lab=$DOCKYARD_LAB`, and publish `127.0.0.1:$DOCKYARD_PORT:8080`.
Do not mount the source directory into this container.
Verify `/healthz` returns release `dispatch-1`.

Check the difference between the image's recorded command and the container's running state.
A successful build alone is not completion.
