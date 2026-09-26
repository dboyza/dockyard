# An HTTP route needs a controller

Ingress describes HTTP host and path routing to Services.
The resource does not forward traffic by itself; an ingress controller watches it and configures a working proxy.
IngressClass identifies the intended controller, which matters when a cluster has more than one implementation.
This lab supplies Traefik so the exercise focuses on route behavior rather than controller installation.

TLS is negotiated before the HTTP request is routed.
The client must trust the certificate and verify that it names the requested hostname.
SNI communicates the requested hostname during TLS negotiation; the later HTTP Host header participates in route selection.
An HTTPS response obtained with `--insecure` does not establish the certificate identity contract.

## Worked example

```sh
kubectl describe ingress dispatch
kubectl get ingressclass traefik
kubectl describe secret dispatch-tls
curl --noproxy '*' --fail --cacert "$DOCKYARD_TLS_CERT" --resolve "dispatch.test:$DOCKYARD_TLS_PORT:127.0.0.1" "https://dispatch.test:$DOCKYARD_TLS_PORT/healthz"
```

The lab creates a self-signed practice certificate outside the workspace and trusts it only for this request.
No system trust store or DNS configuration is changed.
`--resolve` directs this hostname and port to loopback while preserving hostname verification and SNI.
A production certificate lifecycle would also need issuance, renewal, protection of private keys, and operational monitoring.

Ingress supports a stable, widely deployed API but does not receive the same extensibility as Gateway API.
The next lesson separates infrastructure ownership from application route ownership with that newer model.
