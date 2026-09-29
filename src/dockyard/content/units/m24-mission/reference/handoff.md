# Operating handoff

## Symptom and evidence

- kubectl could not connect. `/etc/haproxy/haproxy.cfg` on the worker listed only the first control-plane node, whose API server is stopped.
- The Dispatch Service selected `track: retired`, so it had no endpoints; after fixing that, jobs stayed `queued` because the worker Deployment had 0 replicas.
- The API ran 1 copy, and `kubectl auth can-i get secrets --as=system:serviceaccount:dispatch:dispatch-reader` returned `yes`.

## Repair and verification

1. Regenerated the load balancer configuration with `python -m dockyard.native lb-config`, checked it with `haproxy -c`, and reloaded HAProxy. `kubectl get --raw=/readyz` returned `ok`.
2. Pointed the Service at `track: stable` and scaled the worker to 1.
3. Restored the Role from `identity.yaml`, scaled the API to 2 copies, and created the `dispatch-operations` PDB with `minAvailable: 1`.
4. Set `VERSION` to `dispatch-handoff-v1`, ran `python build.py`, and restarted both Deployments.

To check:

- `kubectl get --raw=/readyz` returns `ok`.
- `kubectl get deployment dispatch worker` shows all copies up to date and available.
- `kubectl get pdb dispatch-operations` allows 1 disruption.
- `kubectl auth can-i` for `dispatch-reader`: `yes` for listing Pods, `no` for Secrets, Deployment changes, and RoleBindings.
- A new job reaches `done`.

## Recovery boundaries and next actions

The first control-plane node's API server and etcd are still stopped; two of three etcd members keep quorum, so losing another control-plane node would stop the API.
The single worker holds the API, the workers, the database's volume, and the load balancer, so losing it stops everything.
Escalate before any further control-plane maintenance, and plan the first node's recovery separately.
