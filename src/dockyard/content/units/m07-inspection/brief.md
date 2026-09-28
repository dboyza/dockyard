## Reconnect the Service to its Pods

Dispatch’s two Pods are running and healthy, but its Service reaches none of them.

1. Compare the Pods’ labels with the Service’s selector, and look at the Service’s EndpointSlices.
2. Fix the selector in `service.yaml`. Do not rename anything or change namespaces.
3. Apply it with `kubectl apply -f service.yaml` and check that the EndpointSlices now list two ready addresses.
4. Use the `kubectl exec` command from Understand to request `http://dispatch:8080/healthz` from inside the cluster.
5. Choose **Check work**.

In your notes, explain why the Service found no Pods even though its name matched the Deployment’s.
