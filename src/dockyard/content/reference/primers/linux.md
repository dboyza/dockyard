# Connect files, processes, services, and permissions

Containers and Kubernetes ultimately rely on Linux processes, filesystems, sockets, and kernel isolation mechanisms.
The administration labs use real owned Ubuntu VMs so you can inspect those layers directly.
Enter the named guest from the lab terminal before using Linux administration commands.

## Files and identity

```sh
id
ls -l /etc/hostname
stat /etc/hostname
```

`id` shows the current user and groups.
A file's owner, group, and mode affect who can read, write, or execute it.
For directories, execute permission allows traversal, while read permission allows listing names.
A numeric container UID is an identity inside its filesystem and permission checks; a matching friendly username is not required for the kernel to enforce ownership.
A mounted file can be present and still unreadable to the application UID.

## Processes and sockets

```sh
ps -eo pid,ppid,user,comm
ss -lnt
```

A PID identifies a process at one moment and may be reused later.
A TCP listening socket identifies an accepting address and port, which is not the same as an application being ready to do useful work.
A Unix socket is a local IPC endpoint such as containerd's `/run/containerd/containerd.sock`.
A Kubernetes API HTTPS endpoint and a CRI Unix socket serve different clients and protocols.
Changing one client endpoint does not automatically repair the other.

## systemd supervises services

```sh
systemctl status containerd --no-pager
systemctl show containerd -p ActiveState -p SubState -p MainPID
sudo journalctl -u containerd -n 20 --no-pager
```

`systemctl` reports and controls service units.
`journalctl` reads journal records, which help explain starts, stops, and failures.
`active` is a service-manager observation, not a complete application test.
`enable` configures startup behavior; `start` changes the current running state.
`restart` stops and starts a service, while `reload` asks a supporting service to reload configuration.
Some configuration changes require `daemon-reload` so systemd rereads unit definitions before a restart.

## Namespaces and cgroups answer different questions

Linux namespaces provide separate views of resources such as processes, networking, and mounts.
Cgroups account for and constrain resources such as CPU and memory.
A container is not a separate kernel in the way a VM is.
In this course, containerd and kubelet use systemd-managed cgroups, and an actual workload PID can be traced through `/proc/PID/cgroup`.
That live path is stronger evidence than a configuration file merely declaring the intended driver.

## Stop at the first unsupported assumption

An application process can survive while kubelet is stopped.
A file can contain the expected bytes while the running process still uses an older configuration.
A certificate can be renewed on disk while the server still presents the previous certificate until its process reloads or restarts.
Observe the running boundary that matters before declaring recovery complete.

## Check your understanding

Distinguish a service unit, its current PID, its socket, and an application request.
Explain which observation you would use to verify each one after a configuration change.
