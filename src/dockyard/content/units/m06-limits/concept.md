## Limit what a container can do

If an attacker ever took control of Dispatch, what could they do with it?
This lesson adds several independent restrictions, each closing a different door.
None of them replaces fixing bugs in the application, but together they limit the damage.

**Who the process runs as.**
Dispatch already runs as user 10001, not root, so it cannot change most files.

**A read-only filesystem.**
`--read-only` makes the container’s own files unchangeable, even for root.
A stateless API such as this one only reads its files, so it works perfectly.
A database is different: it must write its data, so it needs a writable volume for that folder.

**Capabilities.**
Linux splits root’s special powers into separate **capabilities**, such as changing file owners or binding to low port numbers.
Dispatch needs none of them, so `--cap-drop ALL` removes them all.

**No new privileges.**
Some programs are marked to run with extra privileges whenever anyone starts them.
`--security-opt no-new-privileges` stops the container’s processes gaining privileges that way.

**Resource limits.**
Linux **cgroups** limit how much of the computer a group of processes may use.
`--memory 128m` caps memory, `--cpus 0.5` allows at most half of one processor, and `--pids-limit 64` caps the number of processes.
Limits that are too small make the app fail, so always check it still works.

## A worked example

This short-lived container runs one command with limits and is removed afterwards:

```sh
docker run --rm --label "io.dockyard.lab=$DOCKYARD_LAB" \
  --memory 128m --cpus 0.5 --pids-limit 64 \
  "$DOCKYARD_PYTHON_IMAGE" python -c 'print("bounded job")'
```

For the API you will combine all of the options above on your usual long-running `docker run` command, with its name, label, and port mapping.

## Check the limits are really applied

`docker inspect` shows what you asked for.
To see what the container actually enforces, read the limit files inside it:

```sh
docker exec "$DOCKYARD_CONTAINER" cat /sys/fs/cgroup/memory.max /sys/fs/cgroup/cpu.max /sys/fs/cgroup/pids.max
docker exec "$DOCKYARD_CONTAINER" id
```

`memory.max` is in bytes, so 128 MiB appears as `134217728`.
`cpu.max` shows two numbers, such as `50000 100000`, meaning 50,000 microseconds of processor time in every 100,000: half a CPU.

Check work also tries to write a file into the container as root.
A read-only filesystem must refuse it; a mere permission error is not the same thing.

## The same settings in Compose

In the capstone you will apply these restrictions in a Compose file instead.
Each option has a matching Compose setting under the service:

```yaml
    read_only: true
    cap_drop: [ALL]
    security_opt: [no-new-privileges:true]
    mem_limit: 128m
    cpus: 0.5
    pids_limit: 64
```

## When something breaks

If the app fails after you add restrictions, read its logs and think about which restriction it hit.
Relax only that one, and only as much as the evidence justifies.
Removing every limit, running as root, or using `--privileged` would make the problem disappear by throwing away all the protection.
