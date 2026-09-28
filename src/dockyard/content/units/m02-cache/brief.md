## Put your changed release into service

The lab starts with a working image and container serving `dispatch-1`.
Use the sequence in Understand to make a small, visible release change.

1. Change `VERSION` to `dispatch-2` and save it.
2. Request `/healthz` before rebuilding and record the release you see.
3. Rebuild `$DOCKYARD_IMAGE`, compare its ID with the running container’s image ID, and request `/healthz` again.
4. Replace only `$DOCKYARD_CONTAINER` with a new container from the rebuilt image.
   Keep its lab label and local port mapping, and do not mount the workspace.
5. Confirm that `/healthz` now reports `dispatch-2`, then check your work.

Explain why the first two requests still returned the old version.
The checker tests the final release and its packaged files; your intermediate observations are for self-review.
