## Release contract

Package Dispatch as `$DOCKYARD_IMAGE` with release `dispatch-release` in VERSION.
Use a multi-stage build with a source verification step and a final non-root runtime.
The container must serve `/healthz` from its packaged files, not a host bind mount.
It must use the assigned name, lab label, and loopback-bound host port.
The final image must exclude the build's `/source` directory.

Leave the service running and record how another operator would build and run the image using the supplied base-image argument.
Explain which observations establish source version, process identity, and artifact independence.
The runbook explanation is self-review; the required service behavior is checked live.
