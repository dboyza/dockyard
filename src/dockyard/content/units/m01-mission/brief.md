## Service recovery contract

Prepare creates an exited container with a misleading successful exit code.
The supplied app.py is correct and does not need editing.

Restore a long-running Dispatch API using the assigned container name, lab label, and host port.
The endpoint must bind only to 127.0.0.1 and respond on `/healthz` with service `dispatch`.
Preserve other containers and the supplied image.
Leave the corrected instance running.

Record the original configured command, the observed failure mechanism, and the two independent observations that prove recovery in your notes.
Use only commands and concepts already introduced in this module.
