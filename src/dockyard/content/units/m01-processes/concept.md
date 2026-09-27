## Start with something you can see

In this lesson, you’ll start Dispatch and ask whether it is healthy.
You don’t need to understand its Python code.
We’ll focus on how the program runs and how a request reaches it.

A **process** is a running program.
A **container** gives a process its own view of files, networking, and other operating-system resources.
An **image** is the reusable package Docker uses to create that container.
Think of the image as the starting material and the container as one instance made from it.
You can create several containers from the same image.

The important part is that a container needs a main process.
When that process finishes, the container stops.
A container is not a small computer that stays on after its programs have finished.

## What Dispatch does here

Dispatch will eventually accept jobs, process them in the background, and save their results.
For now, we’re using its simplest version: a small web service that answers requests.
An **API** is the part of an application that another program can send requests to.
Dispatch’s `/healthz` address answers with a short message saying the service is working.

To reach it, we need to connect two **ports**, which are numbered destinations for network traffic:

- Dispatch listens on port **8080 inside the container**.
- Your terminal connects to an **assigned port on your computer**.

Docker’s port mapping connects those two destinations.
The numbers do not need to be the same.
The address `127.0.0.1`, also called localhost or loopback, refers to the computer making the request.
We’ll publish the service there so it is available locally.

## Prepare your terminal

Choose **Prepare lab**, then open its terminal or copy the displayed lab command into a terminal you already use.
On Windows, run the lab command in WSL.
Keep that terminal beside this lesson.
It opens in a folder containing `app.py`, the supplied application.

Dockyard sets named values called **environment variables** for this lesson.
The shell replaces a name such as `$DOCKYARD_PORT` with its value when you run a command.
Keep the dollar signs and quotes in the examples; you don’t need to replace them by hand.

- `DOCKYARD_CONTAINER`: the name reserved for this container.
- `DOCKYARD_LAB`: the label value identifying this lab’s resources.
- `DOCKYARD_WORKSPACE`: the folder containing your application files.
- `DOCKYARD_PORT`: the port assigned on your computer.
- `DOCKYARD_PYTHON_IMAGE`: the prepared image containing Python.

Try `pwd` to see the folder and `ls` to list its files.
You can read the supplied application with `cat app.py`, but you don’t need to edit it.

## Start Dispatch

Run this command in the lab terminal.
Each backslash continues the command onto the next line, so you can paste the whole block at once.

```sh
docker run -d \
  --name "$DOCKYARD_CONTAINER" \
  --label "io.dockyard.lab=$DOCKYARD_LAB" \
  -p "127.0.0.1:$DOCKYARD_PORT:8080" \
  -v "$DOCKYARD_WORKSPACE:/app:ro" \
  -w /app \
  "$DOCKYARD_PYTHON_IMAGE" python app.py
```

That is a lot of options for one command, so let’s unpack them:

- `-d` starts the container in the background and returns you to the terminal prompt.
- `--name` gives it this lab’s name, and `--label` marks it as belonging to this lab.
- `-p` connects the assigned local port to port 8080 inside the container.
- `-v` makes your application folder available at `/app` inside the container; `ro` means read-only.
- `-w /app` makes `/app` the working directory inside the container.
- `python app.py` starts the web service and becomes the container’s main process.

Docker prints a long container ID after a successful start.
That tells you Docker started the container, but we still need to find out whether the application works.

## Send a request

```sh
docker ps
docker logs "$DOCKYARD_CONTAINER"
curl "http://127.0.0.1:$DOCKYARD_PORT/healthz"
```

`docker ps` lists running containers.
Look for your assigned name and the port mapping.
`docker logs` shows messages written by the application.
`curl` sends the HTTP request, the same kind of request a browser sends.
You should see `{"service": "dispatch", "status": "ok"}`.
If you ask immediately after starting the container, the application may still be starting; wait a moment and try the request again.

A running container and a successful response tell you different things.
The first means its main process is still running.
The second means a request reached a working service.

## Predict, stop, and try again

Before running the next command, predict what will happen to the health request.

```sh
docker stop "$DOCKYARD_CONTAINER"
curl "http://127.0.0.1:$DOCKYARD_PORT/healthz"
```

The request should now fail because the service is stopped.
Try `docker ps -a` to see stopped containers as well as running ones.
The container still exists, and its image is still available.

Start the same container again, then repeat the health request:

```sh
docker start "$DOCKYARD_CONTAINER"
```

Leave it running and choose **Check work**.
The next lesson looks more closely at what stays the same when you stop and start a container.

## If something goes wrong

If Docker reports a name conflict, this lab’s container already exists.
Inspect it with `docker ps -a` before deciding what to do; you may only need `docker start`.
If it exits straight away, check its logs and the command it was given.
If it runs but the request fails, compare the published ports with the example and look for application errors in the logs.
You can use the first hint if you’re unsure what to inspect next.
