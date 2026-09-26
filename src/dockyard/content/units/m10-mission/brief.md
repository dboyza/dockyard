# Restore four independent paths

Dispatch itself is running, but its internal Service targets the wrong port, the LoadBalancer selects no application Pods, and both ingress and Gateway routes have broken references.
Repair `platform.yaml`, `loadbalancer.yaml`, `ingress.yaml`, and `gateway.yaml`.
Keep the supplied names, explicit hostnames, listener ports, and TLS Secret identity.
Apply the manifests and verify all paths with actual traffic.

The internal DNS destination must reach the owned Dispatch Pods.
The LoadBalancer must allocate a real private-network address and carry a request from the supplied Docker client.
HTTPS for `dispatch.test` must validate the supplied certificate and reach Dispatch.
HTTP for `gateway.dispatch.test` must use an accepted, resolved HTTPRoute, while an unmatched hostname returns 404.

Write a short incident note describing each fault and the observation that proved its repair.
Use an independent retake after any reference-assisted attempt to demonstrate the complete diagnosis without revealed answers.
