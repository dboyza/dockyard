## Find the failed boundary

A connection refusal means no service accepted the connection at the chosen endpoint.
A certificate validation error means the client reached TLS but could not establish the expected trust or server identity.
An HTTP 401 means authentication failed, while a 403 usually means an authenticated request lacked authorization.
These observations lead to different repairs; disabling TLS verification obscures the boundary rather than establishing trust.
A kubeconfig combines an endpoint, CA trust, credentials, and a selected context.
Keep that file private because embedded client keys grant the identity's permissions.

## The control plane beneath kubectl

Kubeadm writes static Pod manifests under `/etc/kubernetes/manifests`.
The local kubelet watches that directory and supervises the API server, controller manager, scheduler, and local etcd through containerd.
Mirror Pod objects expose those workloads through the API, but deleting a mirror object does not remove its source manifest.
CRI inspection remains useful when a particular operator's API client is broken.
A healthy API process still needs a functioning datastore and certificates, so one running process is not a complete readiness check.

## Worked example: inspect server trust

```sh
limactl shell --workdir=/tmp "$DOCKYARD_CONTROL_PLANE"
sudo kubeadm certs check-expiration
sudo openssl x509 -in /etc/kubernetes/pki/apiserver.crt -noout -subject -issuer -dates
sudo openssl verify -CAfile /etc/kubernetes/pki/ca.crt /etc/kubernetes/pki/apiserver.crt
sudo crictl ps
```

The certificate's validity dates, issuing CA, and SANs answer different questions.
`openssl verify` checks trust and validity here; a real API request additionally checks the endpoint's identity and the client's permissions.
Do not print private key material into notes or exported runbooks.
Certificate renewal is taught in the maintenance module; this exercise does not require rotating working credentials.

## Two intentionally separate clients

The host computer uses Dockyard's managed private kubeconfig through a loopback forwarding endpoint.
This lesson also supplies `$HOME/.kube/operator.conf` inside the control-plane guest, which connects directly to the native control-plane endpoint.
Repair the guest client only.
The guest's `/etc/kubernetes/admin.conf` is the authoritative working administrative client supplied by kubeadm, and it should remain root-readable.
A copied operator client should belong to the guest user with mode 600.

## The native checkpoint

Dispatch now runs on two real Ubuntu guests, with containerd and kubeadm rather than kind nodes.
The host terminal keeps its private Kubernetes client; `limactl` opens a separate Linux guest session.
The guest's root account is confined to that app-owned VM, but the external host shell still has your normal user privileges.
No host directories are mounted into either guest.
The database uses a retained local PersistentVolume on the worker, which deliberately has node affinity and is not replicated storage.
The hardened API, queue, worker, and frontend retain the application and access boundaries from the previous phase.

Use `exit` to return from a guest shell to the Dockyard workspace.
The variables `DOCKYARD_CONTROL_PLANE` and `DOCKYARD_WORKER` name this attempt's guests; do not substitute unrelated VM names.
The lab's resource panel shows the recorded guests and their state.
