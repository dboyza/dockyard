## The files now travel with the image

Your container ran without reaching back into your workspace.
If you edit `app.py` now, the running container will not change, because it uses the copy inside the image.
To ship a change, you rebuild the image and replace the container, which the next lesson explores.

Check your understanding:
Which instruction in your Dockerfile runs at build time, and which one only takes effect when a container starts?
Why does adding `EXPOSE 8080` not remove the need for `-p`?
