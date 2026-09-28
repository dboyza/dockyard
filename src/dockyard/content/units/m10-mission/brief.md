## Restore all four paths to Dispatch

The internal Service targets the wrong port, the LoadBalancer selects no Pods, and both the Ingress and the Gateway route have broken references.
Fix `platform.yaml`, `loadbalancer.yaml`, `ingress.yaml`, and `gateway.yaml`, keeping the supplied names, hostnames, ports, and TLS Secret.

When you are done:

- `http://dispatch:8080` from inside the cluster reaches Dispatch.
- The LoadBalancer has an address and answers a request from the Docker-network client.
- HTTPS to `dispatch.test` passes certificate checks and reaches Dispatch.
- `gateway.dispatch.test` reaches Dispatch through an accepted route, and an unmatched hostname returns 404.

Write a short note describing each fault and the request that proved its fix.
