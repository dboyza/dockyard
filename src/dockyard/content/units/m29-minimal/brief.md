## Ship only what Dispatch needs

The Dispatch image runs as root and carries a shell and package managers it never uses, and nobody has checked it for setuid programs.

1. Inspect the running container's user, setuid files, and tools.
2. Rework the `Dockerfile` so the image runs as user `10001`, has no shell, no `apk` or `pip`, no setuid or setgid files, and starts with the exec form.
3. Build with `sh release.sh`, replace the container, confirm Dispatch still answers, and choose **Check work**.

In your notes, explain why a distroless base would be a better long-term answer than removing files yourself.
