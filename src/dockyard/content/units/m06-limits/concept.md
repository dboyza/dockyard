## Several controls solve different problems

A non-root identity reduces authority inside the container.
A read-only root filesystem prevents writes to the image-backed filesystem, even when ordinary file permissions would allow them.
Capabilities divide some traditional root privileges into narrower controls.
The no-new-privileges setting prevents a process from gaining additional privileges through mechanisms such as a set-user-ID executable.
None of these controls replaces fixing an application vulnerability.

Cgroups enforce resource boundaries.
A memory limit bounds memory usage, a CPU quota constrains CPU time, and a process limit bounds how many tasks can exist in the container's cgroup.
An unrealistically small limit can make the application fail, so a successful check must establish both configured constraints and live service behavior.

## Worked example: a bounded batch container

```sh
docker run --rm --label "io.dockyard.lab=$DOCKYARD_LAB" \
  --memory 128m --cpus 0.5 --pids-limit 64 \
  "$DOCKYARD_PYTHON_IMAGE" python -c 'print("bounded job")'
```

The API task uses the same resource ideas but remains running and serves requests.
Its supplied image already uses a non-root user and does not need to write application files during normal requests.
That makes a read-only root filesystem and dropping all capabilities appropriate here.
A database has different write requirements; do not blindly apply an API recipe to every service.

## Observe the applied boundary

Docker inspection reports configured resource and security settings.
Inside a cgroup-v2 container, memory.max, cpu.max, and pids.max report the active limits.
The checker compares these live observations and attempts a narrowly scoped root-filesystem write, which must be rejected as read-only.
A file-permission failure alone would not prove the filesystem was mounted read-only.

## Diagnose constraints without disabling everything

If an application fails, inspect logs, exit status, and the relevant resource boundary.
Increase or change the specific control when evidence justifies it.
Do not remove all limits, run privileged, or switch to root merely to make a failing check disappear.
The next cumulative mission applies deliberate controls to the application roles in the complete stack.
