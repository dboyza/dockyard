## Everything in an image is something an attacker can use

A container image usually carries much more than the application: a shell, a package manager, network tools, and programs with special privileges.
The application never uses them, but an attacker who gets code running in the container will.
A shell lets them run commands.
A package manager lets them install tools.
A **setuid** program runs with its owner's privileges, often root, so it is a classic way to raise their own privileges.
Every extra package is also another source of vulnerabilities for scanners to report and for you to patch.

**Minimizing the base image footprint** means shipping only what the application needs to run.

```figure
image-footprint
```

## Ways to get there

- **Choose a smaller base.** `slim` and `alpine` variants leave out most tools. **Distroless** images go further: they contain the language runtime and its libraries, but no shell or package manager at all.
- **Build in one stage, run in another.**
  A multi-stage build compiles and downloads in a full builder image.
  It then copies only the results into a small final image.
- **Remove what remains.** When you cannot change the base, delete what the application does not need in the final stage, and run as a non-root user.

This lab's Dispatch image is built from the pinned Python image, which is based on **Alpine Linux**.
Alpine is already small, but it still includes a shell, the `apk` package manager, and Python's `pip`.
The work here is the third approach, and the ideas carry over directly to choosing a distroless base.

## Finding what is there

Look inside the image you are running:

```sh
docker exec "$DOCKYARD_CONTAINER" id
docker exec "$DOCKYARD_CONTAINER" ls -l /bin/sh /bin/ls /sbin/apk
docker exec "$DOCKYARD_CONTAINER" find / -xdev -type f -perm /6000
```

`id` shows the container runs as root.
The `ls -l` output shows that `/bin/sh` and `/bin/ls` are links to `/bin/busybox`.
**BusyBox** is a single program that provides about 300 small commands, including the `sh` and `ash` shells, depending on the name it is started by.
Deleting `/bin/sh` alone would leave `/bin/ash` and `busybox sh` working, so the shell only goes away when BusyBox itself does.

`find ... -perm /6000` lists files with the setuid or setgid bit set.
This Alpine image has none, but many base images do: Debian-based images, for example, include setuid copies of `su`, `passwd`, and `mount`.
Check every image you minimize, and keep a step that clears the bits, so a later change of base image cannot quietly bring them back.

## Removing it in the Dockerfile

A final `RUN` step can clear setuid bits and delete tools:

```dockerfile
RUN find / -xdev -type f -perm /6000 -exec chmod a-s {} + \
 && rm -rf /sbin/apk /etc/apk /lib/apk /usr/local/bin/pip* \
 && rm /bin/busybox
USER 10001:10001
```

`chmod a-s` removes the setuid and setgid bits.
`/etc/apk` and `/lib/apk` hold `apk`'s settings and its record of installed packages.
Deleting `/bin/busybox` removes every command linked to it at once; the links stay, but they point at nothing and cannot run.
The shell that runs this step is BusyBox too.
It keeps working until the step ends, even after its own file is deleted, so it can be the last thing removed.
Anything after this step that needs a shell will fail, so put it last.

## Starting without a shell

`CMD python app.py`, the **shell form**, asks Docker to run `/bin/sh -c "python app.py"`.
Without a shell, that container cannot start.
The **exec form**, a JSON list, starts the program directly:

```dockerfile
CMD ["python", "app.py"]
```

```figure
exec-form
```

The application files must stay readable by the new user; `COPY --chown=10001:10001` makes that user their owner.

## Fix it

1. Inspect the running container: its user, its setuid files, and its tools.
2. Change the `Dockerfile` to clear any setuid bits, remove `apk`, `pip`, and BusyBox, run as user `10001`, and start with the exec form.
3. Build with `sh release.sh`, then replace the container with one from the new image.
4. Confirm `docker exec "$DOCKYARD_CONTAINER" sh` now fails, and that `curl "http://127.0.0.1:$DOCKYARD_PORT/healthz"` still answers.

## If something goes wrong

- **The container exits immediately**: the `CMD` is still in shell form, or it names a program that was removed. `docker logs "$DOCKYARD_CONTAINER"` shows the error.
- **The build fails after your removal step**: a later instruction needs a shell. Move the removal step to the end.
- **The shell check still fails after deleting `/bin/sh`**: `/bin/ash` and `/bin/busybox` still run a shell. Delete `/bin/busybox`.
- **The application cannot read its files**: they are owned by root and not readable by `10001`; use `COPY --chown`.
