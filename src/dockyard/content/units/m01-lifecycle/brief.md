## Bring the prepared container online

Dockyard has created Dispatch’s container but has not started it.
The application and its port mapping are already set up.

1. Use `docker ps -a` and `docker inspect` to find the container’s state, ID, command, and port mapping.
2. Start the existing container. Do not use `docker run`; the container already exists.
3. Request `/healthz` at `127.0.0.1:$DOCKYARD_PORT` and confirm Dispatch answers.
4. Stop and start the container again, and compare its ID before and after.
5. Leave it running and choose **Check work**.

Check work tests that the container is running, belongs to this lab, and answers on its port.
It does not see your terminal history, so the ID comparison is for you to confirm.
