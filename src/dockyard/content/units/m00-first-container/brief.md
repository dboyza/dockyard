Let’s run your first container and see what Docker keeps after its program finishes.
Use the commands in Understand as you work through these steps.

1. Prepare the lab and open its terminal.
2. Print `$DOCKYARD_CONTAINER` and `$DOCKYARD_PYTHON_IMAGE` to see the values Dockyard set for you.
3. Run the container from Understand and read the message it prints.
4. Compare `docker ps` with `docker ps -a`, then read the output again with `docker logs`.
5. Leave the stopped container in place and choose **Check work**.

You’re ready to check when `docker ps -a` shows your container as `Exited (0)` and `docker logs` shows `Hello from inside a container`.
In your notes, describe in your own words what the image, the container, and the process each were in this lab.
