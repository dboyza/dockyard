## What changed

The binding that handed anonymous callers read access is gone, and the API server now accepts requests without credentials only for its health endpoints.
Everything else without credentials is rejected at authentication with 401, so even a future careless binding to `system:unauthenticated` would grant nothing outside those paths.

Check your understanding: `kubeadm join` uses anonymous access to read the `cluster-info` ConfigMap when a new node joins.
What would you have to plan for before adding a node to this cluster?
Why does a static Pod need a volume mount to read a file that already exists on its own node?
