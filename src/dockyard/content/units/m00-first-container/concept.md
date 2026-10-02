## Why containers exist

Every program depends on other software to run.
A Python program needs the right version of Python, the libraries it imports, and sometimes particular files or settings.
Your computer has its own collection of that software, and it rarely matches the computer the program was written on exactly.
That mismatch is behind the familiar complaint: “it works on my machine.”

A **container** solves this by packaging a program together with everything it needs, then running that package in its own separate space on your computer.
The program sees the software that came in its package, not whatever happens to be installed around it.

```figure
why-containers
```

You don’t need to install Python, or anything else a container brings with it, for the container to work.
You only need Docker.

## Three words you’ll use in every lesson

Three ideas come up constantly, so let’s define them carefully before using them.

A **process** is a program that is currently running.
You start processes all the time: every command you type in a terminal starts one, and it ends when that command finishes.

An **image** is a read-only package of files: the basic files of an operating system, a language such as Python, and often an application.
An image never runs by itself and never changes.

A **container** is an image brought to life.
Docker makes a private space from the image’s files, then starts a process inside it.
That process sees the image’s files as if they were the whole computer.

A helpful comparison is a document template.
The template (the image) stays untouched.
Each time you use it you get a separate copy (a container) that you can work in, and you can make as many copies as you like.

Step through the figure to see the whole life of a container, from image to finished program.

```figure
image-to-container
```

The most important idea here is the last step.
**A container runs only as long as its main process runs.**
When that process finishes, the container stops.
It is not a small computer that stays switched on afterwards.

## Docker, the tool that runs containers

Docker has two parts that work together.
The `docker` command is what you type in your terminal.
It does not run containers itself; it passes your request to the **Docker Engine**, a background service that stores images and runs containers.

```figure
docker-client-engine
```

Containers rely on features of the Linux operating system.
On macOS and Windows, the Docker Engine therefore runs inside a small Linux virtual machine that Docker manages for you.
You type the same commands either way.

## Prepare your terminal

Choose **Prepare lab**, then open its terminal or copy the displayed lab command into a terminal you already use.
On Windows, run the lab command in WSL.
Keep that terminal beside this lesson.

Dockyard sets a few named values in that terminal, called **environment variables**, so your commands use names reserved for this lab.
When you type a name that starts with a dollar sign, such as `$DOCKYARD_CONTAINER`, the shell replaces it with its value before running the command.
Try it:

```sh
echo "$DOCKYARD_CONTAINER"
echo "$DOCKYARD_PYTHON_IMAGE"
```

`echo` simply prints what it is given, so you see each value.
This lesson uses three of them:

- `DOCKYARD_CONTAINER`: the name reserved for your container.
- `DOCKYARD_LAB`: a label value that marks the container as belonging to this lab.
- `DOCKYARD_PYTHON_IMAGE`: the prepared image containing Linux and Python.

Keep the dollar signs and double quotes exactly as shown in the examples.
You never need to replace them by hand.

The image’s value looks like `python@sha256:` followed by a long string of letters and numbers.
`python` is the image’s name, and the long part is its **digest**, a fingerprint that identifies one exact version of the image.
Dockyard pins that version so every learner gets identical results.

## Look at the image

Ask Docker to list that image:

```sh
docker image ls "$DOCKYARD_PYTHON_IMAGE"
```

You should see one row describing it.
Depending on your Docker version, it shows one size or two: the space the unpacked image takes on disk, and the smaller size of its compressed download.
Dockyard downloaded it when you prepared the lab, so it is already on your computer.

## Run your first container

Now create a container from the image and run one line of Python inside it.
Each backslash at the end of a line continues the command on the next line, so you can paste the whole block at once.

```sh
docker run \
  --name "$DOCKYARD_CONTAINER" \
  --label "io.dockyard.lab=$DOCKYARD_LAB" \
  "$DOCKYARD_PYTHON_IMAGE" \
  python -c "print('Hello from inside a container')"
```

Let’s read it piece by piece:

- `docker run` creates a new container from an image and starts it.
- `--name` gives the container the name reserved for this lab, so you can refer to it later.
- `--label` attaches a small piece of information to the container; here it marks the container as part of this lab.
- `"$DOCKYARD_PYTHON_IMAGE"` is the image to start from. Everything before it configures the container; everything after it is the command to run inside.
- `python -c "print(...)"` runs a single line of Python. That becomes the container’s main process.

You should see `Hello from inside a container`.
That line was printed by a process running inside the container, and Docker passed it through to your terminal.
Your terminal prompt then comes back, because the program finished.

## Where did the container go?

The program has finished, so is the container gone?
Find out:

```sh
docker ps
docker ps -a
```

`docker ps` lists containers that are **running** right now, so yours is not there.
`docker ps -a` lists **all** containers, including stopped ones.
Yours appears with a status such as `Exited (0) 10 seconds ago`.
Its IMAGE column shows a short ID rather than `python`, because the lab names the image by its digest.

The number in brackets is the **exit code**, a number every process reports when it finishes.
Zero means it finished successfully; any other number means something went wrong.

If you have used Docker before, other containers appear too.
Find yours by the name in the NAMES column, or list only yours:

```sh
docker ps -a --filter "name=$DOCKYARD_CONTAINER"
```

The container still exists, with its name, its settings, and a record of what it printed.
Read that record with:

```sh
docker logs "$DOCKYARD_CONTAINER"
```

You see the same message again.
Docker keeps a container, and its logs, until you remove it with `docker rm`.

## Optional: look around inside the image

This command starts a separate, throwaway container that prints a description of the operating system it sees:

```sh
docker run --rm "$DOCKYARD_PYTHON_IMAGE" cat /etc/os-release
```

It reports **Alpine Linux**, even if your computer runs macOS or Windows.
The process inside the container sees the image’s files, not your computer’s.

`--rm` tells Docker to remove the container as soon as its program finishes.
That is handy for quick experiments, but leave it out of the graded run above, or there will be nothing left to check.

## If something goes wrong

- **“Cannot connect to the Docker daemon”**: the Docker Engine is not running. Start Docker Desktop or your Docker service, then try again.
- **“The container name is already in use”**: you have already created this lab’s container. Run `docker ps -a` to look at it. If it printed the wrong message, remove it with `docker rm "$DOCKYARD_CONTAINER"` and run the command again.
- **A Python error such as `SyntaxError`**: check the quotes. The Python code sits inside double quotes, and the message inside single quotes.
