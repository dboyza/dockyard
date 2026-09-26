# Find the empty selector

The Deployment requests two Pods with label `app=dispatch`.
The Service incorrectly selects `app=dispatch-old`, leaving the application unreachable through its Service even when individual Pods are healthy.

1. Inspect Pod labels, the Service selector, and EndpointSlices.
2. Correct the Service selector in `service.yaml` without renaming resources or moving them to another namespace.
3. Apply the file and confirm that EndpointSlices contain ready addresses.
4. From a Dispatch Pod, make a real request to `http://dispatch.dispatch.svc.cluster.local:8080/healthz` using Python's `urllib.request`.
5. Check the lab once both replicas and the Service work.

Use `kubectl exec deployment/dispatch -- python -c 'import urllib.request; print(urllib.request.urlopen("http://dispatch:8080/healthz").read().decode())'` for the request.
