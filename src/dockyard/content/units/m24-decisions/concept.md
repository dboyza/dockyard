## Decisions come with limits

Operating a system means making choices within limits: how much CPU and memory you may use, how much disruption users can tolerate, and who is allowed to do what.
This lesson turns three such limits into Kubernetes settings you can check.

Someone has "helped" by scaling the API down to one copy and giving the inventory tool full access to everything in the namespace.
Your job is to bring both back within the limits below.

## Limit 1: CPU and memory

The team has set these limits for the Dispatch API, across all its copies together:

- between 2 and 4 copies (replicas);
- total CPU **requests** of at most 1 CPU, and total memory requests of at most 512 MiB;
- total memory **limits** of at most 1 GiB;
- every container's limit at least as large as its request.

Remember the difference:
the **request** is what the scheduler reserves on a node for the container, and the **limit** is the most it may use before it is throttled (CPU) or killed (memory).

### Worked example: do the sums before scaling

```sh
kubectl get deployment dispatch -o jsonpath='{.spec.template.spec.containers[0].resources}'; echo
```

Each API container requests `25m` CPU and `32Mi` memory, with limits of `300m` CPU and `192Mi` memory.
`m` means thousandths of a CPU, so `25m` is 0.025 CPU.
With 2 copies: requests are 50m CPU and 64 MiB, and memory limits total 384 MiB.
With 4 copies: 100m CPU and 128 MiB requested, 768 MiB of memory limits.
Both fit, so the existing settings work with anything from 2 to 4 copies.
A fifth copy would still fit the requests, but it is outside the 2 to 4 range the team agreed.

```figure
capacity-sums
```

These numbers are the team's rules for this lab, not measurements.
In real life you would base them on how much the application actually uses, with `kubectl top` and monitoring.

Two copies also do not protect against losing the worker node: both run there, next to the database's volume.
They help during a rolling update or when one Pod crashes.

## Limit 2: how much disruption is allowed

A **PodDisruptionBudget (PDB)** limits *voluntary* disruptions, such as `kubectl drain`, to keep enough copies running.
It does not prevent crashes or node failures.

Create a PDB named `dispatch-operations` that selects the stable API Pods, `app: dispatch` and `track: stable`, and keeps at least one available.
Any of `minAvailable: 1`, `minAvailable: 50%`, or `maxUnavailable: 1` does that with two copies.
The quickest way is the imperative command:

```sh
kubectl create pdb dispatch-operations --selector=app=dispatch,track=stable --min-available=1
kubectl get pdb dispatch-operations
```

With two ready copies, `ALLOWED DISRUPTIONS` should show 1.

## Limit 3: least privilege

The `inventory` Deployment runs as the `dispatch-reader` ServiceAccount.
All it needs is to list Pods in the `dispatch` namespace.
It must not read Secrets, change Deployments, or create RoleBindings.
Its Role, `dispatch-pod-reader`, has been changed to allow everything.

Look at the Role and test what the account can do:

```sh
kubectl get role dispatch-pod-reader -o yaml
kubectl auth can-i list pods --as=system:serviceaccount:dispatch:dispatch-reader
kubectl auth can-i get secrets --as=system:serviceaccount:dispatch:dispatch-reader
kubectl auth can-i patch deployments --as=system:serviceaccount:dispatch:dispatch-reader
```

The correct Role is in `identity.yaml`.
That file contains a `${DOCKYARD_IMAGE}` placeholder, so apply it with `python render.py identity.yaml | kubectl apply -f -`.
You can also edit the Role yourself: it needs one rule allowing `get`, `list`, and `watch` on `pods` in the core API group (`""`).
Keep the same ServiceAccount and RoleBinding, so the real inventory Pod uses your fix.

Check work goes further than `auth can-i`: it uses the inventory Pod's own token to call the API, expecting Pods to be allowed, and Secrets and other namespaces refused.

## Finish

Scale the API to your chosen number of copies, wait for `kubectl rollout status deployment/dispatch`, and confirm a new job still completes.
