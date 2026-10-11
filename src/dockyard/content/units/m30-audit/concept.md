## Who did what, and when

When something goes wrong in a cluster, the first questions are who did it, when, and from where.
Pod logs cannot answer that, because the actions happen at the API server: reading a Secret, deleting a Deployment, creating a RoleBinding.

**Audit logging** makes the API server write a record of requests it handles.
Each record is one line of JSON naming the user, the action, the object, the time, the source address, and the result.
Kubernetes does not audit anything by default; you turn it on with a **policy** that decides what to record.

```figure
audit-pipeline
```

## Audit levels

For each request, the policy chooses one of four levels:

- `None` records nothing.
- `Metadata` records who, what, when, and the result, but no request or response body.
- `Request` adds the body the client sent.
- `RequestResponse` adds the body the API server sent back.

```figure
audit-levels
```

Bodies matter for some questions, such as what exactly changed in a Deployment.
But a Secret's response body *is* the Secret, so logging Secrets at `Request` or `RequestResponse` copies every password into the audit log.
Secrets belong at `Metadata`.

## Writing a policy

A policy is a list of rules.
For each request, the API server takes the **first** rule that matches, so specific rules come before general ones:

```yaml
apiVersion: audit.k8s.io/v1
kind: Policy
omitStages:
- RequestReceived
rules:
- level: None
  resources:
  - group: ""
    resources: ["events"]
- level: Metadata
  resources:
  - group: ""
    resources: ["secrets"]
- level: RequestResponse
  verbs: ["create", "update", "patch", "delete"]
  resources:
  - group: "apps"
    resources: ["deployments"]
- level: Metadata
```

- `group: ""` is the core API group, where Secrets and events live; Deployments are in `apps`.
- `omitStages: [RequestReceived]` writes each request once, when the response starts, rather than also when it arrives.
- The final rule, with no conditions, catches everything else.

The draft in your workspace, `audit-policy.yaml`, has a single rule logging everything at `RequestResponse`.
It would fill the log with Secret contents.

## Turning it on

The API server needs the policy file and somewhere to write, and both must be mounted into its static Pod, as with the configuration files in earlier modules:

```yaml
- --audit-policy-file=/etc/kubernetes/audit/policy.yaml
- --audit-log-path=/var/log/kubernetes/audit/audit.log
- --audit-log-maxage=7
- --audit-log-maxbackup=3
- --audit-log-maxsize=50
```

The last three rotate the log: keep files for 7 days, at most 3 old files, each up to 50 megabytes.
Without them, the log grows until the disk is full.
Mount the policy file read-only with `type: File`, and the log folder writable with `type: DirectoryOrCreate`.

## Reading the log

Each line is a JSON object, so filter it with `grep` and a small Python one-liner on the control plane:

```sh
sudo grep '"resource":"secrets"' /var/log/kubernetes/audit/audit.log | tail -5 | python3 -c 'import json,sys; [print(e["user"]["username"], e["verb"], e["objectRef"].get("namespace"), e["objectRef"].get("name"), e["level"]) for e in map(json.loads, sys.stdin)]'
```

## Fix it

1. Rewrite `audit-policy.yaml` so Secrets are logged at `Metadata` only, workload changes in full, and noise not at all.
2. Install it on the control plane at `/etc/kubernetes/audit/policy.yaml`, and add the audit flags and the two mounts to the API server's manifest.
3. Wait for `kubectl get --raw=/readyz` to print `ok`, then give the cluster a minute to collect events.
4. Something reads the `dispatch-database` Secret every 20 seconds. Find out which identity it is from the audit log, and write its full username, such as `system:serviceaccount:NAMESPACE:NAME`, into `finding.txt` in your workspace.

## If something goes wrong

- **The API server does not come back**: a path in a flag does not match its mount, or the policy file is not valid YAML. `sudo crictl logs` on the newest `kube-apiserver` container names the problem.
- **The log stays empty**: the log folder is not mounted writable, or the policy's first rule matches everything at `None`.
- **Secret entries include `responseObject`**: a rule before your Secrets rule matches them at a higher level. Move the Secrets rule up.
