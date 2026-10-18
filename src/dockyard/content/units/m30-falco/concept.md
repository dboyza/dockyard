## Watching what containers do

Everything so far in this phase has been prevention: settings that stop bad things happening.
Prevention is never complete, so you also need **detection**: noticing when something unexpected happens while workloads run.

**Falco** watches system calls on a node as they happen, enriches each with context such as the container, Pod, and namespace, and checks the stream against **rules**.
When a rule matches, Falco writes an alert.
This is **behavioral detection**.
It does not look for known malware files.
It looks for actions that should not happen, such as a shell starting inside a web server or a process reading a password file.

```figure
falco-pipeline
```

## Running Falco

This lab installed Falco on the worker, together with a systemd unit for it, but it is not running yet.
Falco uses an eBPF program, a small, verified piece of code loaded into the kernel, to see system calls without changing the kernel.

```sh
limactl shell "$DOCKYARD_WORKER" sudo systemctl enable --now falco
limactl shell "$DOCKYARD_WORKER" sudo journalctl -u falco -f
```

`enable --now` starts it and keeps it starting at boot.
Its alerts go to standard output, which systemd stores in the journal; `journalctl -u falco -f` follows them, and Control-C stops following.
Falco ships with default rules in `/etc/falco/falco_rules.yaml`, and loads extra rule files from `/etc/falco/rules.d`.

## Writing a rule

A rule has a name, a condition, an output, and a priority:

```yaml
- rule: Shell in application container
  desc: A shell process started inside a container in an application namespace.
  condition: >
    spawned_process and container
    and proc.name in (sh, bash, dash, ash)
    and k8s.ns.name in (billing, dispatch, frontend)
  output: >
    Shell in application container
    (namespace=%k8s.ns.name pod=%k8s.pod.name command=%proc.cmdline parent=%proc.pname)
  priority: WARNING
```

- `condition` is a filter over each event. `spawned_process` and `container` are **macros** from the default rules: a new program started, inside a container rather than on the host.
- `proc.name`, `k8s.ns.name`, and `k8s.pod.name` are **fields**: facts about the event. Falco gets Pod and namespace names from the container runtime.
- `output` is the alert text; `%field` inserts a field's value, so the alert says exactly which Pod did what.
- `priority` ranks the alert, from `DEBUG` up to `EMERGENCY`.

```figure
falco-rule
```

Open a shell on the worker with `limactl shell "$DOCKYARD_WORKER"` to write and test rules there.
Check a rule file before restarting Falco, loading it with the default rules so their macros are available:

```sh
sudo falco -V /etc/falco/falco_rules.yaml -V /etc/falco/rules.d/dockyard.yaml
```

Then `sudo systemctl restart falco` loads it.

## Fix it

1. Create `/etc/falco/rules.d/dockyard.yaml` on the worker.
   Add a rule that alerts when a shell starts in a container in the `billing`, `dispatch`, or `frontend` namespaces.
   The output must name the namespace and Pod.
2. Validate it with `falco -V`, then enable and start Falco.
3. Follow the alerts. Something keeps starting shells; find which namespace and workload it is.
4. Write it into `finding.txt` in your workspace as `NAMESPACE/NAME`, where `NAME` is the Deployment or the Pod.

## If something goes wrong

- **Falco exits straight away**: `sudo journalctl -u falco -n 30` shows why; a rule file that does not load is the usual cause, so run `falco -V` again.
- **No alerts appear**: check Falco is running with `systemctl status falco`, and that your condition's namespace list includes `billing`. Shells start every fifteen seconds.
- **The alert shows `<NA>` for the Pod**: the event came from the host rather than a container; check your condition includes `container`.
