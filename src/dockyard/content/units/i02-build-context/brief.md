## Ship the current release

Find out why a successful build still produces an image with the old `VERSION`, then fix the cause.

- Build `$DOCKYARD_IMAGE` so it contains the workspace’s current `app.py` and `VERSION`.
- Replace the running container with one from the new image, keeping this lab’s name, label, and port mapping on `127.0.0.1:$DOCKYARD_PORT`.
- Do not mount the workspace into the container; the image must carry the files.
- Leave Dispatch running with `/healthz` reporting `incident-release-v2`.

In your notes, record the symptom, the evidence that pointed to the cause, your fix, and how you confirmed it.
Explain why clearing Docker’s build cache would not have fixed this on its own.
