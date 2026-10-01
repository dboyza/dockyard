## Gateway API: routing with clear ownership

**Gateway API** is the newer way to route traffic into a cluster, and the CKA exam now includes it.
It splits what Ingress did in one object into three, so that different people can own different parts:

| Object | Who usually owns it | What it says |
| --- | --- | --- |
| **GatewayClass** | the cluster’s administrators | which controller implements gateways, here Traefik |
| **Gateway** | the platform team | an entry point: which ports and protocols to listen on, and which routes may attach |
| **HTTPRoute** | an application team | which hostnames and paths go to which Service |

An HTTPRoute **attaches** to a Gateway through `parentRefs`, and sends traffic to Services through `backendRefs`.
Those are two separate links, and either can be broken on its own.

## This lab’s objects

```yaml
kind: Gateway
metadata:
  name: dispatch-gateway
spec:
  gatewayClassName: traefik
  listeners:
  - name: web
    protocol: HTTP
    port: 8080
    allowedRoutes:
      namespaces:
        from: Same
---
kind: HTTPRoute
metadata:
  name: dispatch
spec:
  parentRefs:
  - name: dispatch-gateway
  hostnames:
  - gateway.dispatch.test
  rules:
  - matches:
    - path: {type: PathPrefix, value: /}
    backendRefs:
    - name: dispatch
      port: 8080
```

`allowedRoutes.namespaces.from: Same` means only routes in the Gateway’s own namespace may attach.
The `port` in `backendRefs` is the **Service’s** port, not the container’s port and not a node port.
Routes to a Service in another namespace also need a **ReferenceGrant** in that namespace to allow it; this lab keeps everything in `dispatch`.

## Status conditions tell you what went wrong

Both Gateways and HTTPRoutes report **conditions** in their status:

- **Accepted**: the controller accepted the configuration, or the route was allowed to attach.
- **ResolvedRefs**: everything the route refers to, such as the backend Service and port, exists and is allowed.
- **Programmed**: the Gateway’s configuration has been pushed to the proxy that carries traffic.

```sh
kubectl get gatewayclass,gateway,httproute
kubectl describe gateway dispatch-gateway
kubectl describe httproute dispatch
```

In `describe httproute`, look under **Status → Parents** for the conditions and their messages.
If the route names a Gateway that does not exist, there is no entry under Parents at all: no controller has picked the route up, so nothing reports on it.
An empty Parents list is itself the clue to check `parentRefs`.

```figure
gateway-api
```
Each condition has an `observedGeneration`; if it is lower than the object’s current `generation`, the condition describes an older version and is out of date.

## Test with real requests

The Gateway’s listener is connected to `$DOCKYARD_PORT` on your computer.
The route only matches requests for `gateway.dispatch.test`, so send that name in the `Host` header:

```sh
curl --fail -H 'Host: gateway.dispatch.test' "http://127.0.0.1:$DOCKYARD_PORT/healthz"
curl -i -H 'Host: unmatched.dispatch.test' "http://127.0.0.1:$DOCKYARD_PORT/healthz"
```

The first should reach Dispatch.
The second should get `404 Not Found`, which proves the route is matching hostnames rather than sending everything to Dispatch.

Resist fixing a broken attachment by allowing every namespace or adding a wildcard hostname; that hides the mistake and opens the route to things it should not serve.
