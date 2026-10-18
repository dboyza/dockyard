## Programs that wait for requests

So far, your containers have run a program that finished at once, and one that waited and did nothing.
Most programs you’ll run in containers are a third kind: a **server**, a program that waits for requests from other programs and answers each one.

A **web server** answers **HTTP requests**, the kind of request your browser sends when you open a web page.
Python includes a small web server that shares the files in the folder it starts in:

```sh
python -m http.server 8000
```

To run it in a container, we need to solve two problems.
First, a request from your computer has to reach the server inside the container.
Second, the server needs a web page to share, and the image does not contain one.

## Ports: numbered doors for network traffic

One computer can run many servers at the same time.
Each one listens on a **port**, a number from 1 to 65535 that tells incoming traffic which program it is for.
The command above tells the web server to listen on port 8000.

A container has its own private network, separate from your computer’s.
So port 8000 inside the container is not reachable from your computer until you **publish** it.
Publishing connects a port on your computer to a port inside the container, and Docker forwards every request between them.

```figure
port-publishing
```

You publish a port with `-p`:

```sh
-p "127.0.0.1:$DOCKYARD_PORT:8000"
```

Read it left to right as *“on this computer’s address, connect this port to port 8000 inside the container.”*
The two port numbers do not need to match.
Dockyard assigns a free port on your computer for each lab, in `$DOCKYARD_PORT`, so labs never compete for the same one.

`127.0.0.1` is a special address that always means *this computer*.
It is also called **localhost** or **loopback**.
Publishing on it means only programs on your own computer can connect.
If you leave the address out, Docker publishes on every network your computer is connected to, so other devices on the same Wi-Fi could reach the server too.
We always use `127.0.0.1` for practice.

## Bind mounts: share a folder with a container

Your lab workspace contains a folder called `site` with a small web page in it.
A **bind mount** makes a folder on your computer appear at a path inside the container.
It is not a copy: the container looks directly at your folder, so changes on either side show up immediately.

```figure
bind-mount
```

You add a bind mount with `-v`:

```sh
-v "$DOCKYARD_WORKSPACE/site:/site:ro"
```

The part before the first colon is the folder on your computer, and the part after it is where that folder appears inside the container.
The final `ro` stands for **read-only**: the container can read the files but cannot change them.
Giving a container only the access it needs is a good habit from the very beginning.

## The working directory

Every process starts in some folder, called its **working directory**.
The web server shares whichever folder it starts in, so we use `-w /site` to start it in the mounted folder.

## The whole command

Here is everything together, with each part labeled:

```figure
web-server-command
```

## Try it

Prepare the lab and open its terminal.
Look at the page you are about to serve:

```sh
cat site/index.html
```

Now start the web server:

```sh
docker run -d \
  --name "$DOCKYARD_CONTAINER" \
  --label "io.dockyard.lab=$DOCKYARD_LAB" \
  -p "127.0.0.1:$DOCKYARD_PORT:8000" \
  -v "$DOCKYARD_WORKSPACE/site:/site:ro" \
  -w /site \
  "$DOCKYARD_PYTHON_IMAGE" \
  python -m http.server 8000
```

Check that it is running and see its published port:

```sh
docker ps
docker port "$DOCKYARD_CONTAINER"
```

The PORTS column shows something like `127.0.0.1:54321->8000/tcp`: port 54321 on this computer leads to port 8000 in the container.
Your number will be different.
`docker port` shows the same connection starting from the container’s side: `8000/tcp -> 127.0.0.1:54321`.

If the previous lesson’s container is still running, `docker ps` lists it too, under its own name.
It does no harm, and you can stop that lab from **Lab manager** when you no longer need it.

## Send a request

`curl` sends an HTTP request from the terminal, like a browser that shows you the raw reply instead of drawing a page:

```sh
curl "http://127.0.0.1:$DOCKYARD_PORT/"
```

You should see the HTML of your page, including `Hello from your workspace`.
Every request is recorded in the server’s logs:

```sh
docker logs "$DOCKYARD_CONTAINER"
```

Look for a line containing `"GET / HTTP/1.1" 200`.
`GET /` means the request asked for the main page, and `200` is the HTTP code for success.
The address at the start of the line is not `127.0.0.1`: inside its own network, the server sees the request arriving from Docker, which forwarded it.

You can also open the page in your browser.
Print its address, then copy it into the address bar:

```sh
echo "http://127.0.0.1:$DOCKYARD_PORT/"
```

## Change the page from your computer

Add a line to the page on your computer, then request it again:

```sh
echo "<p>Edited on my computer.</p>" >> site/index.html
curl "http://127.0.0.1:$DOCKYARD_PORT/"
```

`>>` adds the text to the end of the file.
The new line appears straight away, without restarting anything, because the container reads your folder directly.
You can also edit the file with any text editor.

Now try to change the folder from inside the container:

```sh
docker exec "$DOCKYARD_CONTAINER" touch /site/test.txt
```

`touch` tries to create an empty file, and fails with `Read-only file system`.
That is the `ro` option doing its job.

## If something goes wrong

- **`curl` reports “Connection refused”, “Failed to connect”, or “Empty reply from server”**: compare `docker port "$DOCKYARD_CONTAINER"` with the `-p` option above. The number after the arrow must be your assigned port, and the container side must be `8000`.
- **You see a list of files instead of your page**: the server started in the wrong folder. Check the `-v` and `-w` options.
- **The container is missing from `docker ps`**: read `docker logs "$DOCKYARD_CONTAINER"` to see why it stopped.

Ports and mounts are fixed when a container is created.
To change them, remove the container with `docker rm -f "$DOCKYARD_CONTAINER"` and run the full command again.
`-f` stops a running container before removing it.
