## Which Pod answered?

Dispatch runs as two identical replicas behind one Service.
When a request misbehaves, the first question is often which Pod answered it, and on which node.
Logs and error reports are only useful if each Pod can say who it is.

This version of Dispatch has an address for exactly that: `/whereami`.
It reports a Pod name, namespace, node, memory limit, and labels, but it can only report what it is given.
A container does not automatically know its own Pod's details.

## The Downward API

The **Downward API** lets a Pod pass facts about itself down into its own containers.
Kubernetes already knows these facts, because they are stored in the Pod object.
They include its name, namespace, labels, the node it was scheduled to, and each container's resource requests and limits.
The Downward API copies them into the container in one of two ways.

```figure
downward-api
```

### As environment variables

An environment variable can take its value from the Pod with `valueFrom` instead of a fixed `value`:

```yaml
env:
- name: DISPATCH_POD_NAME
  valueFrom:
    fieldRef:
      fieldPath: metadata.name
- name: DISPATCH_MEMORY_LIMIT
  valueFrom:
    resourceFieldRef:
      containerName: api
      resource: limits.memory
```

`fieldRef` reads a field of the Pod, such as `metadata.name`, `metadata.namespace`, or `spec.nodeName`.
`resourceFieldRef` reads a container's requests or limits.
Memory is reported in bytes by default; add `divisor: 1Mi` to report mebibytes instead.

The difference from a fixed `value` matters.
A Deployment stamps out every replica from one template, so `value: dispatch` gives every Pod the same name.
`fieldRef` is filled in separately for each Pod as it is created.

### As files

A `downwardAPI` volume writes the same kind of facts into files:

```yaml
volumes:
- name: podinfo
  downwardAPI:
    items:
    - path: labels
      fieldRef:
        fieldPath: metadata.labels
```

Mounted at `/etc/podinfo`, this produces `/etc/podinfo/labels`, with one `key="value"` line per label.
Labels and annotations can change while a Pod runs, and the kubelet updates these files when they do.
Environment variables never change after the container starts, which is why labels are offered as files.

## See what Dispatch reports now

Prepare the lab, then ask one API Pod what it knows about itself:

```sh
kubectl get pods -l app=dispatch -o wide
kubectl exec deploy/dispatch -c api -- python -c "import urllib.request; print(urllib.request.urlopen('http://127.0.0.1:8080/whereami').read().decode())"
```

Compare the reported `pod` and `node` with the `NAME` and `NODE` columns.
The supplied `platform.yaml` gives every replica the fixed name `dispatch` and leaves the node, memory limit, and labels out entirely.

## Fix it

Edit the API container in `platform.yaml`:

- Give `DISPATCH_POD_NAME`, `DISPATCH_POD_NAMESPACE`, and `DISPATCH_NODE_NAME` their values from `fieldRef`.
- Give `DISPATCH_MEMORY_LIMIT` its value from `resourceFieldRef` for the `api` container's `limits.memory`.
- Add a `downwardAPI` volume with a `labels` item, mounted read-only at `/etc/podinfo`.

Apply it with `sh run.sh`, which also waits for the rollout.
Ask each Pod again, using its name instead of `deploy/dispatch`, and compare the answers with `kubectl get pods -o wide`.
Each Pod should now report its own name and node, a memory limit of `201326592` bytes (192 MiB), and a labels file containing `app="dispatch"`.

## If something goes wrong

- **A Pod reports `null` for a field**: that environment variable or the volume is missing from the container that answers, which is `api`.
- **The rollout fails with a validation error**: check the indentation; `fieldRef` and `resourceFieldRef` sit under `valueFrom`, and `items` sits under `downwardAPI`.
- **The memory limit looks small**: a `divisor` of `1Mi` reports `192`; that is accepted, but it means mebibytes, not bytes.
