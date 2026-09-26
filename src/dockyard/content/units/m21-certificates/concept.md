## Renewal has both a file and a process boundary

A serving certificate binds the API endpoint's identity to a trusted certificate authority.
Its private key stays on the control-plane guest.
Renewing the API certificate should preserve the intended subject alternative names and CA trust while issuing a new leaf certificate.
Replacing the CA is a different operation requiring a coordinated trust migration.
This exercise practices proactive renewal; the initial certificate is valid, so the starter fails because renewal has not yet occurred, not because the cluster is broken.

## Inspect public metadata

```sh
limactl shell --workdir=/tmp "$DOCKYARD_CONTROL_PLANE" sudo kubeadm certs check-expiration
limactl shell --workdir=/tmp "$DOCKYARD_CONTROL_PLANE" sudo openssl x509 -in /etc/kubernetes/pki/apiserver.crt -noout -serial -dates -issuer -ext subjectAltName
```

The expiry report distinguishes kubeadm-managed credentials from externally managed certificates.
Do not copy private keys into the workspace or paste administrative kubeconfigs into notes.
Kubeadm uses existing certificate attributes when renewing this certificate.
Changing a manifest or ConfigMap alone does not prove that an already-running process is serving a different leaf certificate.

## Renew deliberately

Run `sudo kubeadm certs renew apiserver` inside the primary guest.
Inspect the public metadata again and compare the serial number with your first observation.
Renewing this leaf does not require replacing the cluster CA or weakening client verification.
The normal private client should continue to trust the API endpoint.

For a deterministic component restart in this disposable lab, find the actual `kube-apiserver` container with `sudo crictl ps` and stop that specific container with `sudo crictl stop CONTAINER_ID`.
Kubelet reconciles the unchanged static Pod manifest and starts a replacement container.
Expect a brief API interruption on this single-control-plane topology.
Deleting the API's mirror Pod through kubectl is not the same as removing its static manifest.
Do not place backup manifests beside active manifests in kubelet's watched directory.

## Observe the served certificate

Wait for `kubectl get --raw=/readyz` to succeed using normal TLS verification.
The assessment opens a fresh verified TLS connection to the private endpoint and compares the certificate it receives with the public certificate on disk.
The serial must differ from the original, and the original CA must remain unchanged.
It also checks the original cluster identities, stored data, and a fresh application transaction.
This prevents a changed file, an insecure client, or a replacement cluster from masquerading as successful renewal.

Kubelet client certificate rotation and administrative client renewal have different owners and lifecycles.
Inspect each credential's purpose before deciding which renewal action applies.
This lab renews the API serving leaf only; it is not a complete CA rotation or a claim that every cluster credential has been refreshed.
