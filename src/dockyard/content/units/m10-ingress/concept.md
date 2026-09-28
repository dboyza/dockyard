## Route web traffic by name and path

A LoadBalancer Service gives you one address per Service.
Real sites usually want one entry point that sends `shop.example.com` to one app and `api.example.com/v2` to another, over HTTPS.
**Ingress** describes that: rules that route HTTP requests to Services by hostname and path.

An Ingress is only a set of rules.
Something must read them and actually proxy traffic: an **ingress controller**.
This lab runs the **Traefik** controller for you.
An **IngressClass** names a controller, and `ingressClassName` in an Ingress says which controller should handle it.
Without a controller, an Ingress is accepted and does nothing.

## An Ingress, piece by piece

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: dispatch
spec:
  ingressClassName: traefik
  tls:
  - hosts: [dispatch.test]
    secretName: dispatch-tls
  rules:
  - host: dispatch.test
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: dispatch
            port:
              number: 8080
```

- `rules` match a hostname and a path, and send matching requests to a Service and port.
- `pathType: Prefix` matches `/` and everything under it; `Exact` matches only that exact path.
- `tls` tells the controller which Secret holds the certificate for which hostnames. That Secret has the special type `kubernetes.io/tls`, with `tls.crt` and `tls.key` keys.

You can also create one with a single command:

```sh
kubectl create ingress demo --class=traefik --rule="dispatch.test/*=dispatch:8080,tls=dispatch-tls" --dry-run=client -o yaml
```

## What HTTPS actually checks

When you connect over HTTPS, before any web page is exchanged, the server shows a **certificate**.
Your client checks two things:

1. It was issued by someone the client **trusts**.
2. It is for the **hostname** you asked for.

If either check fails, curl refuses to continue.
`--insecure` skips both checks.
That makes the connection encrypted, but you no longer know who you are talking to, so never use it to “fix” a certificate problem.

This lab made a practice certificate for `dispatch.test` and saved it at `$DOCKYARD_TLS_CERT`.
Your computer does not know that hostname, so the test uses two curl options:

```sh
curl --noproxy '*' --fail --cacert "$DOCKYARD_TLS_CERT" \
  --resolve "dispatch.test:$DOCKYARD_TLS_PORT:127.0.0.1" \
  "https://dispatch.test:$DOCKYARD_TLS_PORT/healthz"
```

- `--cacert` tells curl to trust this one practice certificate, for this request only.
- `--resolve` says “for this request, `dispatch.test` means 127.0.0.1”, without changing your computer’s settings. curl still checks the certificate is for `dispatch.test`.
- `--noproxy '*'` stops any proxy settings on your computer from getting in the way.

## Inspecting it

```sh
kubectl get ingressclass
kubectl describe ingress dispatch
kubectl describe secret dispatch-tls
```

`describe ingress` shows each rule and the backend it resolves to; a backend that points at a missing Service or port shows up here.

Ingress is stable and very widely used.
The next lesson introduces **Gateway API**, its newer, more flexible successor, which the CKA now also covers.
