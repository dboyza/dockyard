## Repair the forwarding contract

Prepare starts Dispatch from a known-good image but forwards the assigned host port to the wrong container port.
Inspect the running process, logs, and port mapping to identify the mismatch.
Replace only the assigned container with one that forwards `127.0.0.1:$DOCKYARD_PORT` to the actual 8080 listener.
Keep its lab label and packaged application, without a workspace mount.

Leave `/healthz` returning release `dispatch-1` and record which side of the original mapping was wrong.
