## Everything on a node is something to defend

A Kubernetes node needs only a few things to do its job: the kubelet, a container runtime such as containerd, the network plugin, and the operating system underneath.
Every other service, open port, and user account is extra **attack surface**: one more way in for an attacker, and one more thing to keep patched.
Reducing a host to what it needs is called minimizing its **footprint**.

```figure
host-footprint
```

## Surveying a node

Start by finding out what is there.
Open a shell on the worker with `limactl shell "$DOCKYARD_WORKER"`, then list the services that are running:

```sh
systemctl list-units --type=service --state=running --no-pager
```

Each line is a **systemd unit**, a service systemd starts and supervises.
Many are part of Ubuntu itself, such as `systemd-journald` and `ssh`.
Look for anything that does not belong on a Kubernetes node.

Next, list the ports something is listening on:

```sh
sudo ss -ltnp
```

`-l` shows listening sockets, `-t` TCP, `-n` numbers instead of names, and `-p` the process that owns each one, which needs `sudo`.
The `Local Address:Port` column matters: `127.0.0.1` is reachable only from the node itself, while `0.0.0.0` or `*` accepts connections from anywhere that can reach the node.

```figure
listening-ports
```

To learn what a service is, read its unit file and its status:

```sh
systemctl cat report-share
systemctl status report-share --no-pager
```

## Turning a service off for good

Three commands, each doing a different job:

- `sudo systemctl stop NAME` stops it now, but it starts again at the next boot.
- `sudo systemctl disable NAME` stops it starting at boot, but leaves it running now; `disable --now` does both.
- `sudo systemctl mask NAME` links the unit to nothing, so it cannot be started at all, even by another service that depends on it.

Removing the software entirely is even better when nothing else needs it.

## Accounts with power

User accounts are another kind of footprint.
An account that can log in and run `sudo` without a password is, in effect, root.
Find who can use `sudo` with:

```sh
sudo ls /etc/sudoers.d
sudo sudo -l -U backup
```

To retire an account without deleting files that may still matter, remove its sudo rule, set its shell to `/usr/sbin/nologin`, and lock its password:

```sh
sudo rm /etc/sudoers.d/backup
sudo usermod --shell /usr/sbin/nologin --lock backup
```

## Fix it

1. Survey the worker's running services and listening ports, and identify the one that serves files to the whole network.
2. Stop it, make sure it cannot start again, and confirm its port is closed with `ss`.
3. Find the account with passwordless `sudo`, and retire it.

Leave the kubelet, containerd, and SSH alone; the node and this lab need them.

## If something goes wrong

- **The port is still open after `disable`**: `disable` alone does not stop a running service. Use `disable --now`, or `stop` as well.
- **The node turns NotReady**: a service the node needs was stopped. `sudo systemctl start kubelet containerd` on the worker brings them back.
- **`systemctl mask` reports that the unit file already exists**: the service was installed directly in `/etc/systemd/system`, where masking would need to replace it. Disable and stop it, then delete that file and run `sudo systemctl daemon-reload`.
- **`sudo -l -U backup` still lists commands**: another file in `/etc/sudoers.d`, or a line in `/etc/sudoers`, also grants it. `sudo grep -r backup /etc/sudoers /etc/sudoers.d` finds it.
