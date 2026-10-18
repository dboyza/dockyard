## A checklist for a secure cluster

A Kubernetes cluster has dozens of settings that affect security, spread across the API server, the kubelets, etcd, and the files on every node.
Nobody remembers them all, so the industry keeps a shared checklist.
The **CIS Kubernetes Benchmark**, published by the Center for Internet Security, lists recommended settings, explains why each matters, and says how to check and fix it.
Each recommendation has a number, such as 4.2.1, and is marked Automated when a tool can check it or Manual when a person must judge it.

**kube-bench** is an open-source tool that runs those checks.
It reads the processes, command-line flags, and configuration files on the node where it runs.
It compares them with the benchmark.
It reports each check as PASS, FAIL, WARN, or INFO, with advice on how to fix it.

```figure
cis-benchmark
```

## Running kube-bench

kube-bench must run on the node it checks, as root, because it reads protected files.
This lab installed it on both nodes.
Open a shell on a node with `limactl shell`:

```sh
limactl shell "$DOCKYARD_WORKER" sudo kube-bench run --targets node --benchmark cis-1.12
```

`--targets node` checks the worker settings, mostly the kubelet; `--targets master` checks the control-plane components on `$DOCKYARD_CONTROL_PLANE`.
Normally kube-bench picks the benchmark that matches the cluster's version.
This version of kube-bench does not know Kubernetes 1.37 yet, so `--benchmark cis-1.12` names the newest benchmark it has.
Most checks still apply unchanged.
`--check 4.2.1,4.2.2` runs only the checks you name, which keeps the output short.

The report lists each check, then a remediation section for every FAIL and WARN, then totals.
A fresh kubeadm cluster does not pass every check: some recommendations are deliberately left to the operator, such as enabling audit logging, which a later lesson covers.
A benchmark is a starting point for decisions, not a score to maximize blindly.

## The kubelet's own API

Every kubelet runs an HTTPS API on port 10250.
The API server uses it to fetch logs, run `kubectl exec`, and read metrics.
Two settings in `/var/lib/kubelet/config.yaml` decide who else may use it:

```yaml
authentication:
  anonymous:
    enabled: false
authorization:
  mode: Webhook
```

`anonymous.enabled: true` treats any request without credentials as the user `system:anonymous`.
`mode: AlwaysAllow` approves every request.
Together, they let anything that can reach port 10250, including any Pod in the cluster, list Pods and run commands in them.
`mode: Webhook` instead asks the API server whether the caller may do what it asks, using the same RBAC rules as the rest of the cluster.

```figure
kubelet-api-access
```

The kubelet reads its configuration only when it starts, so restart it after editing:

```sh
limactl shell "$DOCKYARD_WORKER" sudo systemctl restart kubelet
```

To see the settings the running kubelet actually uses, ask the API server for that node's live configuration:

```sh
kubectl get --raw "/api/v1/nodes/lima-$DOCKYARD_WORKER/proxy/configz"
```

## API server profiling

The API server can serve Go profiling data at `/debug/pprof`, which helps developers find performance problems.
In production it reveals internal details and gives a way to make the server do expensive work, so CIS check 1.2.15 asks for `--profiling=false`.

The API server is a **static Pod**: the kubelet on the control-plane node runs it from the file `/etc/kubernetes/manifests/kube-apiserver.yaml`.
Add the flag as one more item in the container's `command` list.
When the file changes, the kubelet stops the old API server and starts a new one, so `kubectl` stops answering for a minute or so.
Wait until `kubectl get --raw=/readyz` prints `ok` again.

## Fix it

1. Run kube-bench on the worker with `--check 4.2.1,4.2.2`, and on the control plane with `--targets master --check 1.2.15`, and read the remediation text.
2. On the worker, set `anonymous.enabled` to `false` and `authorization.mode` to `Webhook` in `/var/lib/kubelet/config.yaml`, then restart the kubelet.
3. On the control plane, add `- --profiling=false` to the API server's command in its manifest, then wait for the API to return.
4. Run both kube-bench commands again; each check should now PASS.

Use `sudo nano` or `sudo vi` inside `limactl shell` to edit the files, and keep the YAML indentation exactly as it was.

## If something goes wrong

- **The worker turns NotReady after the restart**: the kubelet could not read its configuration. Run `sudo journalctl -u kubelet -n 30` on the worker; a YAML mistake is named there.
- **kubectl stays unreachable after editing the manifest**: the API server is not starting. On the control plane, `sudo crictl ps -a --name kube-apiserver` shows its attempts, and `sudo crictl logs` on the newest one shows why.
- **A check still FAILs**: the file changed but the process did not. Restart the kubelet, or confirm the API server Pod's command with `kubectl get pod -n kube-system -l component=kube-apiserver -o yaml`.
