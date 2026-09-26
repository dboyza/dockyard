# A stable address still needs a working backend

A ClusterIP Service gives clients a stable virtual address and DNS name while its selected Pods can change.
EndpointSlices describe the backend addresses and readiness used by that Service.
The Service's `port` is the client-facing port, while `targetPort` identifies the application listener in a selected Pod.
A container's declared `containerPort` documents a port; it does not make a process listen there.

NodePort exposes the Service on a node port, usually in the 30000-32767 range.
This lab maps node port 30080 to the Mac's assigned loopback port, so it can be tested without changing host routes.
A LoadBalancer Service asks a load balancer implementation to establish an external destination.
Without such an implementation, a Service can remain Pending indefinitely even though its YAML was accepted.

The prepared lab uses MetalLB to allocate an address on this cluster's private Docker network and announce it to neighboring clients.
That is real load balancer traffic, not an external-IP field inserted by the checker.
The Docker network lives inside Docker's Linux environment on macOS, so a temporary Docker client on that network tests the external address.
The Mac uses the supplied loopback mapping to test NodePort directly.

## Worked example

```sh
kubectl get service dispatch dispatch-node dispatch-public
kubectl get endpointslices -l kubernetes.io/service-name=dispatch
kubectl get pods -l app=dispatch -o wide
curl --fail "http://127.0.0.1:$DOCKYARD_PORT/healthz"
```

To test the LoadBalancer, read its IP and run the supplied cached client:

```sh
LB_IP=$(kubectl get service dispatch-public -o jsonpath='{.status.loadBalancer.ingress[0].ip}')
docker run --rm --label "io.dockyard.lab=$DOCKYARD_LAB" --network "$DOCKYARD_NETWORK" "$DOCKYARD_BUSYBOX_IMAGE" wget -qO- "http://$LB_IP:8080/healthz"
```

A headless Service sets `clusterIP: None` and returns backend addresses instead of providing a virtual-IP load balancing destination.
The StatefulSet module uses that different discovery contract.
