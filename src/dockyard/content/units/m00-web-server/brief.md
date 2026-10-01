Let’s serve the page in your workspace from a container and reach it from your computer.
Use the commands in Understand as you work through these steps.

1. Prepare the lab, open its terminal, and look at `site/index.html`.
2. Start the web server with its port published on `127.0.0.1` and the `site` folder mounted read-only.
3. Request the page with `curl`, then find that request in `docker logs`.
4. Add a line to the page on your computer and request it again.
5. Confirm that the container cannot write to the mounted folder.
6. Leave the server running and choose **Check work**.

You’re ready to check when `curl "http://127.0.0.1:$DOCKYARD_PORT/"` returns your page.
Keep the `Hello from your workspace` heading in the page; add to it rather than replacing it.
In your notes, explain what `127.0.0.1:$DOCKYARD_PORT:8000` connects, and why your edit appeared without a restart.
