## Bring the API server back

- The API server on the control-plane node cannot start. kubectl will only report that it cannot connect.
- From inside the control-plane VM, use `crictl` and the API server's log to find the cause.
- Fix the API server's manifest; keep all certificate checking in place and do not rebuild the cluster.
- Wait until the API is ready and a new Pod is scheduled, for example with `python wait-control-plane.py`.

In your notes, copy the log line or setting that told you what to fix.
