## Do containers share files?

In the last lesson you created one container from the Python image.
Many containers can be made from the same image at once.
That raises a practical question: if one container changes a file, do the others see the change?
To answer it, we need to look at how an image is built and where a container keeps its changes.

## An image is a stack of layers

An image is not one big file.
It is a stack of **layers**, where each layer adds or changes some files on top of the ones beneath it.
You can list the layers of the prepared image:

```sh
docker history "$DOCKYARD_PYTHON_IMAGE"
```

Read the output from the bottom up.
The bottom layer adds the basic files of Alpine Linux, a small Linux distribution.
Layers above it install some system packages and then Python itself.
Rows showing `0B` change settings rather than files, so they add no size.

```figure
image-layers
```

Every layer in an image is **read-only**.
Nothing a container does can change them, which is what makes it safe for many containers to share one image.

## Each container gets its own writable layer

When Docker creates a container, it adds one more layer on top of the image: a thin, empty **writable layer** that belongs to that container alone.
The process inside sees the image layers and its writable layer combined, as one ordinary set of folders.
When it creates or changes a file, the change goes into its writable layer, and the image underneath stays exactly as it was.

Step through the figure to follow a single change.

```figure
writable-layers
```

Removing a container deletes its writable layer, and anything stored there goes with it.
That is why you should never keep important data only inside a container.
A later module shows how to store data safely outside one.

## Keep a container running

To look inside a container, we need one that stays running.
Remember: a container runs only as long as its main process.
`sleep infinity` is a program that waits forever and does nothing else, which makes it a convenient main process for exploring.

We also add `-d`, short for **detached**.
It starts the container in the background and gives you your terminal prompt back, instead of attaching your terminal to a program that never finishes.

## Run a second process inside a running container

`docker exec` starts an extra process inside a container that is already running.
That process sees the same files as the main process, including the writable layer.

```figure
exec-process
```

When the extra process finishes, the container keeps running, because its main process is still there.

## Try it

Prepare the lab, then start a container that stays running:

```sh
docker run -d \
  --name "$DOCKYARD_CONTAINER" \
  --label "io.dockyard.lab=$DOCKYARD_LAB" \
  "$DOCKYARD_PYTHON_IMAGE" \
  sleep infinity
docker ps
```

Docker prints a long container ID, and `docker ps` lists your container as `Up`.

See which processes are running inside it:

```sh
docker exec "$DOCKYARD_CONTAINER" ps
```

Process number 1 is `sleep infinity`, the main process.
The other line is `ps` itself, the extra process that `docker exec` just started.

Now write a file inside the container, then read it back:

```sh
docker exec "$DOCKYARD_CONTAINER" sh -c 'echo "written in the first container" > /tmp/note.txt'
docker exec "$DOCKYARD_CONTAINER" cat /tmp/note.txt
```

`sh -c` runs a small shell command inside the container.
We need it because the `>` symbol, which saves output to a file, must be handled inside the container rather than by your own terminal.

## Find the change

`docker diff` compares a container with the image it came from and lists what its writable layer changed:

```sh
docker diff "$DOCKYARD_CONTAINER"
```

You should see two lines:

```text
C /tmp
A /tmp/note.txt
```

`A` means a file was **added**, and `C` means a folder was **changed**, here because a new file appeared in it.
A `D` would mean something from the image was **deleted** in this container.

## Compare with a fresh container

Start a second, throwaway container from the same image and look for the note:

```sh
docker run --rm "$DOCKYARD_PYTHON_IMAGE" cat /tmp/note.txt
```

It reports `No such file or directory`.
The new container started from the unchanged image with its own empty writable layer, so it has no note.
Your first container still has its note; check with `docker exec` if you like.

## Optional: open a shell inside the container

You can also work inside a container interactively:

```sh
docker exec -it "$DOCKYARD_CONTAINER" sh
```

`-i` keeps the connection open for your typing, and `-t` gives you a proper terminal.
Your prompt changes because you are now typing into a shell running inside the container.
Try `ls /tmp` and `cat /etc/os-release`, then type `exit` to come back.
Leaving the shell ends only that extra process; the container keeps running.

## If something goes wrong

- **The container is not in `docker ps`**: its main process finished. Check that `sleep infinity` came after the image name, then remove it with `docker rm "$DOCKYARD_CONTAINER"` and run it again.
- **The terminal seems stuck after `docker run`**: you probably left out `-d`. Press Control-C, remove the container, and run it again with `-d`.
- **“The container name is already in use”**: run `docker ps -a`. If the existing container is running, you can keep using it. If it has exited, remove it and run it again.
