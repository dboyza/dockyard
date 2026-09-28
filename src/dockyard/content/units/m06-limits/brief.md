## Lock down the API

Dockyard has started a working Dispatch API with none of these restrictions.
Replace it with a container that:

- has a read-only filesystem, all capabilities dropped, and no-new-privileges set;
- is limited to between 32 and 256 MiB of memory, at most one CPU, and between 16 and 256 processes (128 MiB, 0.5 CPU, and 64 processes is a good choice);
- still runs as a non-root user, with this lab’s name, label, and `127.0.0.1:$DOCKYARD_PORT:8080`.

Check that `/healthz` still answers and that the limit files inside the container show your values.
In your notes, explain why this API can run with a read-only filesystem and no extra writable folder.
