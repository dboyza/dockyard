## What survived, and why?

The process was replaced, but its database stayed in the host directory mounted at `/data`.
The image, container, and data directory have separate lifetimes.

Compare your recorded job identity before and after replacement.
Then predict what would happen if the replacement mounted a new, empty directory at the same path.
A mount at the right path is not enough if it points to the wrong storage.
