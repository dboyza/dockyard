## Filtering system calls

A program does almost everything through **system calls**: requests to the kernel to open a file, start a process, change a file's permissions, or open a network connection.
Linux has more than 300 of them, and an ordinary application uses only a fraction.
Many kernel vulnerabilities are reached through system calls that applications never need.

**seccomp**, short for secure computing mode, lets a process carry a filter that the kernel checks on every system call.
The filter can allow a call, refuse it with an error, or kill the process.
A container's filter is set when it starts and applies to everything running inside it.

```figure
seccomp-filter
```

AppArmor, from the previous lesson, decides which files and resources a program may use.
seccomp decides which kernel operations it may ask for at all.
They complement each other.

## Three ways to choose a profile

A container chooses its seccomp profile in its `securityContext`:

```yaml
securityContext:
  seccompProfile:
    type: RuntimeDefault
```

- `Unconfined` applies no filter at all.
- `RuntimeDefault` applies the container runtime's built-in profile, which blocks dozens of rarely needed and dangerous calls while letting ordinary applications run. It is the sensible minimum for every container.
- `Localhost` applies a profile file of your own, stored on the node.

Kubernetes runs containers `Unconfined` unless you ask otherwise, so a Pod with no `seccompProfile` has no filter.
The Restricted Pod Security standard, which you met earlier, requires `RuntimeDefault` or `Localhost`.

```figure
seccomp-profile-types
```

## A profile of your own

The workspace file `profiles/no-chmod.json` is a small Localhost profile:

```json
{
  "defaultAction": "SCMP_ACT_ALLOW",
  "syscalls": [
    {
      "names": ["chmod", "fchmod", "fchmodat", "fchmodat2"],
      "action": "SCMP_ACT_ERRNO",
      "errnoRet": 1
    }
  ]
}
```

`defaultAction` applies to any call not listed: here, allow it.
The rule then refuses the four calls that change file permissions, returning error number 1, `EPERM`, "Operation not permitted".
The processor never needs to change permissions, and an attacker who drops a file often wants to make it executable.

This profile blocks only what it lists, so it is easy to write but stops only what you thought of.
The opposite style, `"defaultAction": "SCMP_ACT_ERRNO"` with a list of allowed calls, is much stronger and much harder to get right; tools exist that record which calls an application makes so you can build one.

The kubelet looks for Localhost profiles under `/var/lib/kubelet/seccomp` on the node running the Pod, and `localhostProfile` is a path relative to that folder:

```yaml
seccompProfile:
  type: Localhost
  localhostProfile: profiles/no-chmod.json
```

As with AppArmor, every node that might run the Pod needs the file.

## Checking a running container

A process's seccomp state is in its status file:

```sh
kubectl exec -n processing deploy/processor -- grep Seccomp: /proc/1/status
```

`Seccomp: 0` means no filter; `Seccomp: 2` means a filter is active.

## Fix it

1. Check both containers' seccomp state; both report `0`.
2. Copy `profiles/no-chmod.json` to `/var/lib/kubelet/seccomp/profiles/no-chmod.json` on both nodes, creating the folder with `sudo mkdir -p`.
3. In `processing.yaml`, give the processor the Localhost profile in place of `Unconfined`, and give `intake` the `RuntimeDefault` profile.
4. Apply with `python render.py processing.yaml | kubectl apply -f -` and wait for both rollouts.
5. Confirm both report `Seccomp: 2`, and that `kubectl exec -n processing deploy/processor -- python -c "import os; open('/tmp/f','w').close(); os.chmod('/tmp/f', 0o755)"` now fails with `Operation not permitted`.

## If something goes wrong

- **The Pod fails with `CreateContainerError`**: the profile file is missing or invalid on the node it was scheduled to. Check the path under `/var/lib/kubelet/seccomp` on that node, and that the JSON is complete.
- **`chmod` still works**: the processor is not using your profile. Check `localhostProfile` is relative, `profiles/no-chmod.json`, not an absolute path.
- **The processor stops writing results**: the profile blocks something it needs; that should not happen with this profile, so compare your file with the original.
