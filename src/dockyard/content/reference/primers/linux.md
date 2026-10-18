# Linux essentials

Containers are Linux processes with some extra isolation, and Kubernetes nodes are Linux machines.
This guide covers the Linux ideas the course relies on: users and permissions, processes, ports, services, and the isolation features that make containers work.

## Users and groups

Every process runs as a **user**, and every user belongs to one or more **groups**.
Linux identifies them by number: the **UID** (user ID) and **GID** (group ID).
UID 0 is **root**, the all-powerful administrator.

```sh
id
```

`id` prints your UID, GID, and groups.
Inside a container, the numbers are what count: a container running as UID 10001 needs no named user for Linux to enforce permissions.

## File permissions

```sh
ls -l
ls -ln
```

A typical line looks like this:

```text
-rw-r----- 1 10001 10001 12288 Sep 28 10:00 jobs.db
```

The first column is the **mode**.
Ignore its first character, which shows the type (`-` for a file, `d` for a directory).
The next nine characters are three groups of three:

| Characters | Who | Here |
| --- | --- | --- |
| `rw-` | the file’s owner | can read and write |
| `r--` | members of the file’s group | can read only |
| `---` | everyone else | no access |

`r` is read, `w` is write, `x` is execute (run it as a program), and `-` means that permission is missing.
`ls -l` shows owner and group names; `ls -ln` shows their numbers.

For a **directory**, `r` lets you list its names, `w` lets you create and delete files in it, and `x` lets you go into it at all.

### Changing permissions and owners

```sh
chmod u+w jobs.db      # give the owner (u) write permission
chmod go-w jobs.db     # take write away from group (g) and others (o)
chmod 600 jobs.db      # the same rules as numbers: owner rw, nobody else
chown 10001:10001 /data
```

Numeric modes add up read = 4, write = 2, execute = 1 for each of owner, group, and others.
So `600` is owner read and write, and `755` is owner everything, everyone else read and enter.

```figure
file-mode-bits
```

`chown` changes owner and group, and usually needs root.

Resist `chmod 777`, which lets every user change the file.
Give the one user that needs access exactly what it needs.

## Processes

A **process** is a running program.
Each has a process ID, or **PID**, and a parent that started it.

```sh
ps -eo pid,ppid,user,comm
```

This lists every process with its PID, its parent’s PID, its user, and its command.
PIDs get reused, so a number only identifies a process while it is running.

## Ports and listening

A server **listens** on a port, waiting for connections.

```sh
ss -lnt
```

This lists listening TCP ports.
A listening port shows something accepted the connection; it does not prove the application behind it is ready to do useful work.

Programs on the same machine can also talk through a **Unix socket**, a special file such as `/run/containerd/containerd.sock`.

## Services and systemd

On most Linux servers, a program called **systemd** starts background services and restarts them if they fail.
Kubernetes components such as the kubelet and containerd run this way.

```sh
systemctl status containerd --no-pager
sudo journalctl -u containerd -n 20 --no-pager
```

`systemctl status` shows whether a service is running and its recent log lines.
`journalctl -u NAME` shows that service’s logs.

- `systemctl start` / `stop` / `restart` changes whether it is running now.
- `systemctl enable` makes it start automatically at boot.
- After editing a service’s definition file, run `systemctl daemon-reload` so systemd reads the change.

“active (running)” means systemd sees the process running, not that the service is working correctly.

## What makes a container

A container is not a small virtual machine; it shares the host’s Linux kernel.
Two kernel features create the isolation:

- **Namespaces** give a process its own view of things such as the process list, network, and files. That is why a container sees only its own processes and has its own `localhost`.
- **cgroups** (control groups) limit and measure resources such as memory and CPU. That is how memory and CPU limits work.

```figure
container-shared-kernel
```

Every process’s cgroup is visible in `/proc/PID/cgroup`, which shows which limits actually apply to it.

## Check the thing that matters

Linux often has several layers that can disagree.
A file can hold a new setting while the running program still uses the old one.
A certificate can be renewed on disk while the server still presents the previous one until it restarts.
After a change, check the running process or a real request, not just the file.

```figure
file-vs-running
```

## Check your understanding

What does `-rw-------` mean, and which command would let the owner write to a file showing `-r--------`?
A service shows “active (running)”. What else would you check before calling it healthy?
