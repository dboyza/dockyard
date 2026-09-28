## Put the application inside its image

In module 1, you mounted `app.py` from your computer into a general Python image.
That works for experiments, but anyone else who wanted to run Dispatch would need a copy of your folder too.
In this lesson you’ll build an **application image**: one that already contains Dispatch’s files and knows how to start it.

Building an image and running a container are two separate steps.
You build once, then run as many containers from that image as you like.

## The Dockerfile

A **Dockerfile** is a plain text file containing the recipe for an image.
Docker follows it from top to bottom.
These are the instructions you need today:

- `FROM` picks the starting image, here one that already contains Python.
- `WORKDIR` sets the folder that later instructions, and the running program, work in.
- `COPY` copies files from your folder into the image.
- `RUN` runs a command while the image is being built, for example to install something.
- `CMD` records the command a container should run when it starts. Nothing runs during the build.

Each instruction that changes files adds a **layer**, a saved snapshot of just those changes.
An image is a stack of layers; the next lesson shows how Docker reuses them to make rebuilds faster.

## Edit the Dockerfile

The workspace already contains a `Dockerfile` with a single comment in it.
Open it in any text editor and save your changes there.
If you are using a terminal editor, `nano Dockerfile` is a simple choice: Control-O then Enter saves, and Control-X exits.
Check what you saved with `cat Dockerfile`.
The terminal guide shows another way to write a file if no editor is installed.

## A worked example

Here is a Dockerfile for a different program, a one-off `report.py` script:

```dockerfile
ARG BASE_IMAGE
FROM ${BASE_IMAGE}
WORKDIR /tool
COPY report.py ./
CMD ["python", "report.py"]
```

`ARG BASE_IMAGE` declares a value you supply at build time, and `FROM ${BASE_IMAGE}` uses it.
Dockyard supplies a specific Python image so everyone builds on exactly the same starting point.
Your Dispatch Dockerfile will follow the same pattern, but with `/app`, both of Dispatch’s files, and Dispatch’s start command.

Build it like this:

```sh
docker build --build-arg "BASE_IMAGE=$DOCKYARD_PYTHON_IMAGE" -t "$DOCKYARD_IMAGE" .
docker image ls "$DOCKYARD_IMAGE"
```

`--build-arg` supplies the `BASE_IMAGE` value, and `-t` gives the new image a name, called a **tag**.
Docker may warn that `BASE_IMAGE` has no default value; that is expected here, because you always supply it.
Read the last lines of the output to confirm the build succeeded before you run anything.

## Which files can a build see?

The final `.` in the build command is the **build context**: the folder whose files Docker is allowed to copy.
`COPY` can only use files inside it.
A `.dockerignore` file in that folder lists files to leave out, such as passwords, caches, or large folders the image does not need.

## Ports are still chosen at run time

A Dockerfile can include `EXPOSE 8080`.
That only documents which port the application uses; it does not make it reachable from your computer.
You still publish the port with `-p` when you run the container, exactly as in module 1.
