## What just happened?

You ran a real application in a container and reached it from your computer.
The image supplied Python, Docker created a container from it, and `python app.py` was its main process.
The port mapping carried your request from your computer to that process.

Check your understanding:
What would happen if you removed the container but kept the image?
If you ran the same image with a command that prints one line and finishes, why would the container stop straight away even though you used `-d`?
If either answer feels uncertain, repeat the stop and start steps and look at `docker ps -a`.

The next lesson looks at stopping, removing, and recreating containers in more detail.
