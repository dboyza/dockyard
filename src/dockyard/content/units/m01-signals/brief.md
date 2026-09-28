## Stop Dispatch cleanly

Dockyard has started a working Dispatch container for this exercise.

1. Request `/healthz` successfully, then find that request’s `200` line in the container’s logs.
2. Stop the container with `docker stop`.
3. Check its final state and exit code with `docker ps -a` or `docker inspect`.
4. Leave the stopped container in place and choose **Check work**.

Use `docker stop` in your terminal, not Dockyard’s Stop lab button: that button pauses the whole practice lab, and Check work cannot run while the lab is paused.
Do not remove the container, because its state and logs are what Check work reads.
