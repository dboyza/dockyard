## The tool can depend on the broken component

Kubectl requires a reachable API server for most of its work.
Repeatedly asking it for cluster events cannot diagnose an API process that fails before becoming ready.
Move to the recorded primary guest and inspect systemd, the CRI runtime, and static manifests there.
Those paths do not require a working Kubernetes API.

This fixture changes the API server's etcd endpoint from local port 2379 to unused port 2399.
The API process cannot establish its datastore connection even though the etcd member still runs.
Do not rebuild the cluster or weaken TLS verification to repair an endpoint typo.
The original certificates, etcd data, and worker application volume remain intact.

## Worked example: follow the failed dependency

```sh
limactl shell --workdir=/tmp "$DOCKYARD_CONTROL_PLANE" sudo crictl ps -a --name kube-apiserver
limactl shell --workdir=/tmp "$DOCKYARD_CONTROL_PLANE" sudo crictl ps --name etcd
limactl shell --workdir=/tmp "$DOCKYARD_CONTROL_PLANE" sudo cat /etc/kubernetes/manifests/kube-apiserver.yaml
limactl shell --workdir=/tmp "$DOCKYARD_CONTROL_PLANE" sudo ss -lntp
```

Use `sudo crictl logs CONTAINER_ID` on a recent failed API container to inspect its connection error.
Compare the `--etcd-servers` argument with etcd's listening address in its own manifest.
A refused connection differs from a certificate verification failure or an authorization denial.
Repair the dependency actually supported by the evidence.

Write the corrected API manifest to a temporary file outside the watched directory and atomically replace the active file.
Correct the endpoint to `https://127.0.0.1:2379`; retain its existing CA and client-certificate arguments.
Kubelet reconciles the changed static Pod without needing the API to be healthy first.
Allow that reconciliation to finish before judging the repair.

## Separate recovery claims

`kubectl get --raw=/readyz` establishes the API's readiness endpoint responds.
A new scheduler assignment establishes another control-plane action.
Original object UIDs distinguish recovery from replacement, and an actual persisted job checks the application boundary.
The assessment combines these observations rather than equating an open TCP port with a recovered cluster.

The supplied `python wait-control-plane.py` helper retries a read and a write against the recovering API, then observes a fresh scheduler assignment before deleting its disposable Pod.
Its source is available in the workspace so you can inspect the exact observations.
The scheduler may need longer to recover its watches and leadership than the API needs to answer a readiness request.
You may perform equivalent explicit checks yourself.
