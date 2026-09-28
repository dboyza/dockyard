## Configuration reaches the process in two ways

The environment variable was fixed when the container started; the banner file could change while it ran.
The ConfigMap itself was fine all along; the problem was how the Deployment used it.

Check your understanding:
After editing a ConfigMap, which kind of consumer needs a rollout restart, and which only needs the application to reread its file?
How would you create this ConfigMap with one `kubectl create configmap` command?
