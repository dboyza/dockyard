# Repair three request paths

The ClusterIP and NodePort Services target port 9090 even though Dispatch listens on 8080.
The LoadBalancer Service selects an application label that no Pod has.

Inspect each route before editing, then repair `platform.yaml`, `nodeport.yaml`, and `loadbalancer.yaml`.
Keep Service names and the assigned NodePort intact.
Apply the manifests, compare EndpointSlices with actual Pod IPs, and test all three request paths.
The public Service must have an assigned address and carry a real request from the private-network client.
An ExternalIP value alone is insufficient.

Use `kubectl exec deployment/dispatch -c api -- python -c 'import urllib.request; print(urllib.request.urlopen("http://dispatch:8080/healthz").read().decode())'` for the ClusterIP request.
