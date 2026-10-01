## What just happened?

Your request travelled from `curl` to your assigned port on `127.0.0.1`, and Docker forwarded it to port 8000 inside the container, where the web server answered.
The server found your page through a read-only bind mount, so it saw your edit at once but could not change your files.

Check your understanding:
What would happen to the request if you had published `-p "127.0.0.1:$DOCKYARD_PORT:9000"` instead?
If a classmate on the same Wi-Fi tried to open your page, why would it fail?
What would the server share if you left out `-w /site`?

You now know every part of a typical `docker run` command: a name and label, a published port, a mounted folder, a working directory, an image, and a main process.
The module’s mission asks you to use them on your own.
