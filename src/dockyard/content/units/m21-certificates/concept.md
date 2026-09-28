## Renewing the API server’s certificate

kubeadm issues certificates that expire after one year.
If they expire, components stop trusting each other and the cluster breaks.
Renewing them before that happens is routine maintenance, and a CKA topic.

The API server’s **serving certificate** proves to clients that they are talking to the real API server.
Its **private key** never leaves the control-plane node.
Renewing it issues a new certificate, with a new serial number, signed by the same cluster **CA**, and keeping the same names (SANs) it is valid for.
Replacing the CA itself is a much bigger job, because every client must learn to trust the new one.

In this lab the certificate is still valid; you are renewing it early, as you would on a maintenance schedule.

## Look at the current certificate

```sh
limactl shell --workdir=/tmp "$DOCKYARD_CONTROL_PLANE" sudo kubeadm certs check-expiration
limactl shell --workdir=/tmp "$DOCKYARD_CONTROL_PLANE" sudo openssl x509 -in /etc/kubernetes/pki/apiserver.crt -noout -serial -dates -issuer -ext subjectAltName
```

`check-expiration` lists every kubeadm-managed certificate and when it expires.
The `openssl` command shows the serial number, validity dates, issuer, and the names the certificate covers.
Write down the serial number.
Never copy private keys or administrator kubeconfigs into your notes.

## Renew it

Inside the control-plane VM:

```sh
sudo kubeadm certs renew apiserver
```

Look at the certificate again: the serial number should have changed, and the issuer should be the same.
`sudo kubeadm certs renew all` renews every kubeadm certificate at once.

## Make the API server use it

Renewing writes a new file, but the running API server still has the old certificate loaded.
It only picks up the new one when it restarts.

The API server is a static Pod, so the kubelet restarts it if its container stops.
Find the real container and stop it:

```sh
sudo crictl ps --name kube-apiserver
sudo crictl stop CONTAINER_ID
```

The kubelet starts a fresh container from the same manifest, which loads the new certificate.
Expect the API to be unavailable for a few seconds.

Deleting the API server’s Pod with kubectl would not do this: that Pod is only a mirror, and the kubelet keeps the real one running from its manifest.
Also, never leave backup copies of manifests in `/etc/kubernetes/manifests`; the kubelet would try to run them too.

## Check the certificate being served

Wait for `kubectl get --raw=/readyz` to succeed, with normal certificate checking.
Check work connects to the API server and compares the certificate it actually receives with the renewed file: the serial must be new and the CA unchanged.
That catches a renewed file the server has not loaded yet.

This lab renews only the API server’s serving certificate.
The kubelet’s own certificates, and the certificates inside kubeconfig files, are renewed separately, so check which credential you are dealing with before choosing how to renew it.
