# Separate infrastructure from routing intent

GatewayClass selects a controller implementation.
A Gateway configures listeners and the rules governing which routes may attach.
An HTTPRoute describes application matching and forwarding, then requests attachment through parentRefs.
This separation lets infrastructure operators manage shared entry points while application teams manage their own routes.
It is an ownership model, not a guarantee that an organization has configured RBAC correctly.

The supplied Gateway listens on HTTP port 8080 inside the controller.
The controller Service maps that listener through node port 30080 to the assigned host computer loopback port.
The HTTPRoute matches `gateway.dispatch.test` and forwards to Service `dispatch` port 8080.
Backend references use the Service port, not the container port or NodePort.

## Follow the conditions

```sh
kubectl get gatewayclass,gateway,httproute
kubectl describe gateway dispatch-gateway
kubectl describe httproute dispatch
curl --fail -H 'Host: gateway.dispatch.test' "http://127.0.0.1:$DOCKYARD_PORT/healthz"
curl -i -H 'Host: unmatched.dispatch.test' "http://127.0.0.1:$DOCKYARD_PORT/healthz"
```

Accepted describes whether the controller accepts the requested configuration or route attachment.
ResolvedRefs describes whether referenced resources are valid and permitted.
Programmed describes whether a Gateway configuration has been sent to the data plane.
Compare observedGeneration with the current resource generation so an old condition cannot masquerade as evidence for a recent edit.
Even current positive conditions need a real request to establish application behavior.

Listeners can restrict route namespaces through allowedRoutes.
Cross-namespace backend references additionally need a ReferenceGrant in the target namespace when supported by the API.
This exercise keeps both resources in dispatch and permits same-namespace attachment.
Do not broaden namespace access merely to hide a misspelled parent reference.
