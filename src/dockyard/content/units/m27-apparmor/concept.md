## Limiting what a process may touch

Containers share their node's kernel.
Namespaces and cgroups decide what a container can see and how much it may use.
But a process running as root inside a container can still do a great deal if it escapes its intended behavior.
This can happen, for example, through a bug in code that parses untrusted files.

**AppArmor** is a Linux security module, which is part of the kernel.
It checks every file access, program run, and network use against a **profile**.
A profile is a list of what one program may do.
When a profile is in **enforce** mode, the kernel refuses anything the profile does not allow, even for root.
In **complain** mode it only logs what it would have refused, which helps while writing a profile.

```figure
apparmor-profile
```

## Reading a profile

Your workspace holds `dockyard-processor`, a profile written for the document processor:

```text
profile dockyard-processor flags=(attach_disconnected,mediate_deleted) {
  #include <abstractions/base>
  /** rix,
  /data/** rw,
  /tmp/** rw,
  deny /etc/** w,
  network inet stream,
  network inet6 stream,
}
```

- `profile dockyard-processor` names the profile; Pods will refer to it by this name.
- `#include <abstractions/base>` pulls in rules almost every program needs, such as reading shared libraries.
- `/** rix` allows reading (`r`) any file and running (`x`) any program, which then inherits (`i`) the same profile.
- `/data/** rw` and `/tmp/** rw` allow writing in the processor's work area; `**` matches any depth of subfolders.
- Anything not allowed is refused, so writes everywhere else fail; `deny /etc/** w` says so explicitly for `/etc`, which also records each refusal in the kernel log.
- The two `network` lines allow ordinary TCP connections.

## Loading a profile on the nodes

The kernel on each node enforces profiles, so each node must have the profile loaded.
A Pod can run on any node, so load it on all of them:

```sh
limactl shell "$DOCKYARD_WORKER" sudo tee /etc/apparmor.d/dockyard-processor < dockyard-processor > /dev/null
limactl shell "$DOCKYARD_WORKER" sudo apparmor_parser --replace /etc/apparmor.d/dockyard-processor
limactl shell "$DOCKYARD_WORKER" sudo aa-status | grep dockyard
```

`tee` writes the file on the node from the copy in your workspace.
`apparmor_parser --replace` compiles the profile and loads it into the running kernel, replacing any older version.
Files in `/etc/apparmor.d` are loaded again automatically when the node starts, so the profile survives a reboot.
`aa-status` lists the loaded profiles and their modes.
Repeat the commands for `$DOCKYARD_CONTROL_PLANE`.

```figure
apparmor-loading
```

## Applying it to a container

A container chooses its profile in its `securityContext`:

```yaml
securityContext:
  appArmorProfile:
    type: Localhost
    localhostProfile: dockyard-processor
```

`type: Localhost` means "a profile already loaded on the node", named by `localhostProfile`.
`RuntimeDefault` would use the container runtime's general-purpose profile instead, and `Unconfined` turns AppArmor off.
If the named profile is not loaded on the node, the container is not started, and `kubectl describe pod` explains why.
That is deliberate: a missing profile should stop the workload, not let it run unprotected.

To check a running container, read its own AppArmor status from inside:

```sh
kubectl exec -n processing deploy/processor -- cat /proc/1/attr/apparmor/current
```

`unconfined` means no profile; `dockyard-processor (enforce)` means it is confined.

## Fix it

1. See the problem: `kubectl exec -n processing deploy/processor -- sh -c 'echo test > /etc/test && echo written'` succeeds, because the processor runs as root with no profile.
2. Load `dockyard-processor` on both nodes and confirm it with `aa-status`.
3. Add the `appArmorProfile` to the processor container's `securityContext` in `processing.yaml`, keeping `runAsUser: 0`.
4. Apply it with `python render.py processing.yaml | kubectl apply -f -` and wait for the rollout.
5. Repeat step 1; the write should now fail with `Permission denied`, while `kubectl logs -n processing deploy/processor` shows documents still being processed.

## If something goes wrong

- **The new Pod stays in `Blocked` or `CreateContainerError`**: the profile is not loaded on the node it was scheduled to. Load it there, then delete the stuck Pod so it is recreated.
- **`apparmor_parser` reports a syntax error**: the file was changed or truncated on the way. Compare it with the workspace copy.
- **The processor stops logging**: the profile refuses something it needs. Look for `apparmor="DENIED"` lines with `sudo journalctl -k | grep DENIED` on the node.
