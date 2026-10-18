## When a container is not enough

Every container on a node shares the node's Linux kernel.
AppArmor and seccomp limit what a container may ask of that kernel.
But a bug in the kernel itself, reachable through a permitted system call, can still let a process escape its container.
For code you do not trust at all, such as customer-supplied templates or plugins, a stronger boundary helps.

A **sandboxed runtime** puts a second kernel between the container and the node.
**gVisor** is one.
Its `runsc` runtime starts each Pod inside a sandbox.
In that sandbox, a user-space kernel called the Sentry handles the container's system calls itself.
It asks the real kernel for only a small, fixed set of operations.
Another approach, Kata Containers, runs each Pod in a lightweight virtual machine.

```figure
sandbox-kernel
```

The cost is speed and compatibility: system calls take longer, and a few unusual ones are not supported.
That is why sandboxes are used for specific risky workloads, not for everything.

## How Kubernetes chooses a runtime

The container runtime on each node, containerd here, can know several **runtime handlers**.
`runc` is the ordinary one; `runsc` is gVisor's.
A **RuntimeClass** object gives a handler a Kubernetes name, and a Pod asks for it with `runtimeClassName`:

```yaml
apiVersion: node.k8s.io/v1
kind: RuntimeClass
metadata:
  name: gvisor
handler: runsc
scheduling:
  nodeSelector:
    sandbox.dockyard.io/gvisor: "true"
```

`handler` must match a handler name in containerd's configuration on the node.
`scheduling.nodeSelector` is added to every Pod that uses this RuntimeClass, so those Pods are only scheduled to nodes with that label.
That matters when only some nodes have the sandbox installed.

```figure
runtimeclass-flow
```

## Setting up the worker

This lab installed the gVisor binaries on both nodes, but containerd does not know about them yet.
Register the handler on the worker by adding a section to `/etc/containerd/config.toml`, then restart containerd:

```toml
[plugins."io.containerd.cri.v1.runtime".containerd.runtimes.runsc]
  runtime_type = "io.containerd.runsc.v1"
```

`runtime_type` names gVisor's containerd shim, `containerd-shim-runsc-v1`, which containerd finds on the node's `PATH`.
Restarting containerd does not stop running containers.
`sudo crictl info | grep -A2 runsc` on the worker confirms containerd now knows the handler.

Then label the worker so the RuntimeClass's selector matches it:

```sh
kubectl label node "lima-$DOCKYARD_WORKER" sandbox.dockyard.io/gvisor=true
```

## Seeing the sandbox

Inside a gVisor sandbox, `dmesg`, which normally shows the node kernel's messages, shows gVisor's own start-up messages instead:

```sh
kubectl exec -n untrusted deploy/template-preview -- dmesg
```

Run it before and after your change to see the difference.

## Fix it

1. Run `dmesg` in the `template-preview` container, and see the node kernel's messages, or a permission error.
2. Register the `runsc` handler in containerd's configuration on the worker, and restart containerd.
3. Label the worker `sandbox.dockyard.io/gvisor=true`, and create the `gvisor` RuntimeClass.
4. Set `runtimeClassName: gvisor` in the Pod template in `untrusted.yaml`, and apply it with `python render.py untrusted.yaml | kubectl apply -f -`.
5. Run `dmesg` again; it should mention gVisor, and the preview service should still answer on port 8000.

## If something goes wrong

- **The new Pod stays `Pending`**: no node matches the RuntimeClass's `nodeSelector`. Check the worker's label with `kubectl get node --show-labels`.
- **The Pod fails with `no runtime for "runsc" is configured`**: containerd on that node does not know the handler. Check the section header is spelled exactly, then restart containerd.
- **The worker turns NotReady after the restart**: containerd failed to read its configuration. `sudo journalctl -u containerd -n 20` on the worker names the line.
