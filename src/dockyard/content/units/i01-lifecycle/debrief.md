## Compare your diagnosis

`launch.sh` started Dispatch in the background with `&`, printed its message, and finished.
The shell running the script was the container’s main process, so when it finished, Docker stopped the container and took Dispatch with it.
Running the server in the foreground, ideally with `exec python app.py` so it replaces the shell, keeps the container alive as long as Dispatch runs.

A restart policy would only repeat the same short-lived launch, and changing ports would not affect it at all.

Check your understanding:
Which piece of evidence first pointed you at the script rather than the network?
What could a team watch for so they notice this kind of failure before users do?
