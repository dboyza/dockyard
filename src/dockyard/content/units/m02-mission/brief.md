## Deliver a portable Dispatch release

Package Dispatch as `$DOCKYARD_IMAGE` with `dispatch-release` in `VERSION`.
Use a first build stage to check the Python source and a separate final stage to run it as a non-root user.
The final image should contain the application files in `/app` and no `/source` directory.

Run it as `$DOCKYARD_CONTAINER` with the lab ownership label and `127.0.0.1:$DOCKYARD_PORT:8080` port mapping.
It must answer `/healthz` from files inside its image, without mounting your workspace.
Leave the service running for Check work.

Write down how another person could build and run this release using the supplied base-image argument.
Explain how you checked the release version, running user, and independence from your local files.
Those explanations are for self-review; a passing runtime check does not grade them.
