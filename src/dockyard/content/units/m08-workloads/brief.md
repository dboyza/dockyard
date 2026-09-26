# Run workers and one agent per eligible node

Dispatch's API, database, and Redis are prepared, but the worker Deployment requests zero replicas and the DaemonSet has an impossible node selector.

1. Inspect the controller and Pod state before changing it.
2. Request two worker replicas in `worker.yaml`.
3. Remove the impossible `dockyard.invalid/node: missing` constraint from `agent.yaml`.
4. Apply the manifests and wait for the worker Deployment and DaemonSet rollouts.
5. Submit a job through the API and inspect a worker's completion log.

The checker submits a unique real job and verifies its result and worker identity.
It also requires one available DaemonSet Pod on every currently eligible node.
