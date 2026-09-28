## Package Dispatch

The workspace contains Dispatch’s `app.py` and `VERSION` files, ready to use.

1. Write a Dockerfile that accepts `BASE_IMAGE`, copies both files into `/app`, and starts Dispatch with `python app.py`.
2. Build it as `$DOCKYARD_IMAGE`, supplying `BASE_IMAGE=$DOCKYARD_PYTHON_IMAGE`.
3. Run a container from your image named `$DOCKYARD_CONTAINER`, with the label `io.dockyard.lab=$DOCKYARD_LAB` and the port mapping `127.0.0.1:$DOCKYARD_PORT:8080`.
   Do not mount your workspace this time: the files should come from the image.
4. Check that `/healthz` reports release `dispatch-1`, then choose **Check work**.

A successful build is only half the job; the task is complete when a container from your image answers requests.
