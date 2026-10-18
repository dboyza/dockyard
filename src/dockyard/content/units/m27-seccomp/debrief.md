## What changed

`intake` now runs with the container runtime's default seccomp filter.
The processor runs with your own profile.
It allows what the default would, but refuses every way of changing file permissions.
Both still do their jobs; the processor simply cannot make a dropped file executable any more.

Check your understanding: why does Kubernetes treat a Pod with no `seccompProfile` as `Unconfined`, and what setting changes that default for a whole node?
How would you find out which system calls the processor really needs before writing an allowlist profile?
