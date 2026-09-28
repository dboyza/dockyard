## Keep the fake secret out of the image

Dockyard has built and started an image whose `COPY . .` includes the fake `.env` file.

1. Change the build so `.env` never enters the image, using `.dockerignore` or by copying only `app.py` and `VERSION`.
2. Rebuild `$DOCKYARD_IMAGE` with `--platform "$DOCKER_DEFAULT_PLATFORM"`.
3. Replace `$DOCKYARD_CONTAINER` with one from the new image, keeping the lab label and `127.0.0.1:$DOCKYARD_PORT:8080`.
4. Check the new image’s platform and that `/healthz` still reports `dispatch-1`.

Leave the fake `.env` in your workspace, and do not copy it in and delete it later.
