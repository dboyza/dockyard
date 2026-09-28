## Restore Dispatch and keep it running

Find out why the container exits straight after its successful launch message, then fix the cause.

- Keep this lab’s container name, label, and port mapping on `127.0.0.1:$DOCKYARD_PORT`.
- Rebuild `$DOCKYARD_IMAGE` from the workspace after your change, and replace the stopped container.
- Leave Dispatch running and answering `/healthz`.

In your notes, record the symptom, the evidence that pointed to the cause, your fix, and how you confirmed it.
Changing the port or adding an automatic restart would not fix the cause; explain why.
