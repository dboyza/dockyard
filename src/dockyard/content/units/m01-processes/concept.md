## Meet Dispatch

From here to the end of the course, you’ll work on one application called **Dispatch**.
Working on one application, rather than a new example in every lesson, means each skill builds on the last.
It also means problems behave the way they do in real systems: a change you make in one module can matter several modules later.

Dispatch is a small **background job** service.
You send it a job, a short piece of text, and it accepts the job straight away.
A separate program then does the work in the background: it converts the text to uppercase and records a fingerprint of it.
Later, you ask Dispatch for the job and see whether it has finished, and with what result.

Real applications use this pattern for work that takes too long to make someone wait for, such as sending emails, resizing photos, or generating reports.
Step through the figure to follow one job through the finished system.

```figure
dispatch-system
```

When it is complete, Dispatch has four parts:

- The **API**, short for application programming interface, is the part other programs send requests to. It accepts jobs and answers questions about them.
- The **database**, PostgreSQL, stores every job, its status, and its result, so nothing is lost if a program restarts.
- The **queue**, Redis, passes short notifications from the API to the worker, so the worker knows new work has arrived.
- The **worker** takes queued jobs, does the work, and records the result.

We supply all of Dispatch’s code, which is written in Python.
You won’t need to write or change any Python.
Your job is the one platform and operations engineers do: run the application, connect its parts, keep it healthy, and fix it when something breaks.

## How Dispatch grows through the course

You won’t meet all four parts at once.
Dispatch starts small and grows as you learn the skills each part needs.

```figure
dispatch-journey
```

## Today: Dispatch’s first version

In this lesson, Dispatch is only its API, and the API can’t take jobs yet.
It answers two addresses:

- `/` replies that Dispatch is ready to accept jobs.
- `/healthz` replies that the service is healthy.

An address like `/healthz` is called a **health endpoint**.
It exists so that people and tools can quickly ask a service whether it is working.
You’ll check it constantly, and in later modules other programs will check it for you.

The API is a web server, just like the one you ran in the foundations.
It listens on port 8080 inside its container, and its code is the file `app.py` in your lab workspace.

```figure
dispatch-first-run
```

## Prepare your terminal

Choose **Prepare lab** and open the lab terminal, as before.
This time the workspace contains `app.py`, Dispatch’s code.
You can read it with `cat app.py` if you’re curious, but you don’t need to understand it.

The lab sets the same variables you used in the foundations, including `$DOCKYARD_CONTAINER`, `$DOCKYARD_LAB`, `$DOCKYARD_PORT`, `$DOCKYARD_WORKSPACE`, and `$DOCKYARD_PYTHON_IMAGE`.

## Start Dispatch

```sh
docker run -d \
  --name "$DOCKYARD_CONTAINER" \
  --label "io.dockyard.lab=$DOCKYARD_LAB" \
  -p "127.0.0.1:$DOCKYARD_PORT:8080" \
  -v "$DOCKYARD_WORKSPACE:/app:ro" \
  -w /app \
  "$DOCKYARD_PYTHON_IMAGE" python app.py
```

You know every option here from the web server lesson.
Only three things are different:

- `-p` connects your assigned port to **8080**, the port Dispatch listens on.
- `-v` mounts the **whole workspace** at `/app`, read-only, so the container can see `app.py`.
- The main process is **`python app.py`**, which starts Dispatch.

Docker prints a long container ID after a successful start.
That tells you Docker started the container, but not yet whether Dispatch works.

## Send a request

```sh
docker ps
docker logs "$DOCKYARD_CONTAINER"
curl "http://127.0.0.1:$DOCKYARD_PORT/healthz"
```

`docker ps` should list your container as `Up`, with your port mapping.
`docker logs` should show `Dispatch listening on 0.0.0.0:8080`, a message Dispatch prints when it starts.
`0.0.0.0` means it accepts connections on every network inside its container, which is what lets Docker forward your requests to it.

The health request should return:

```text
{"service": "dispatch", "status": "ok"}
```

This is **JSON**, a common text format for data: each name in quotes is paired with a value.
Here it says the service is `dispatch` and its status is `ok`.
If you ask immediately after starting the container, Dispatch may still be starting; wait a moment and try again.

Try the main address too:

```sh
curl "http://127.0.0.1:$DOCKYARD_PORT/"
```

## Running is not the same as working

A running container and a successful response tell you different things.
`Up` in `docker ps` means the main process is still running.
A successful health response means a request actually reached a working service.
You’ll meet plenty of situations later in the course where the first is true and the second is not, so always check both.

## Predict, stop, and try again

Before running the next commands, predict what will happen to the health request.

```sh
docker stop "$DOCKYARD_CONTAINER"
curl "http://127.0.0.1:$DOCKYARD_PORT/healthz"
```

The request should now fail, because nothing is listening behind the published port.
Run `docker ps -a`: the container still exists, in the `Exited` state, and the image is still on your computer.

Start the same container again, then repeat the health request:

```sh
docker start "$DOCKYARD_CONTAINER"
curl "http://127.0.0.1:$DOCKYARD_PORT/healthz"
```

Leave it running and choose **Check work**.
The next lesson looks more closely at what stays the same when you stop and start a container.

## If something goes wrong

If Docker reports a name conflict, this lab’s container already exists.
Inspect it with `docker ps -a` before deciding what to do; you may only need `docker start`.
If it exits straight away, check its logs and the command it was given.
If it runs but the request fails, compare `docker port "$DOCKYARD_CONTAINER"` with the `-p` option above, and look for errors in the logs.
