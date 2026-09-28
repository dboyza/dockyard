## What stayed the same?

Starting the container ran a fresh copy of its program, but the container itself did not change.
Its ID, image, and port mapping were all kept from when it was created.

Check your understanding:
Why does `docker run` with a name that is already in use report a conflict, instead of starting the existing container?
If you needed Dispatch on a different host port, why would a restart not be enough?
