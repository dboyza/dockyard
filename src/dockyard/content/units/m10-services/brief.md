## Fix three ways of reaching Dispatch

- The ClusterIP Service `dispatch` and the NodePort Service `dispatch-node` both send traffic to port 9090, but Dispatch listens on 8080.
- The LoadBalancer Service `dispatch-public` selects a label no Pod has.

1. Inspect each Service and its EndpointSlices before changing anything.
2. Fix `platform.yaml`, `nodeport.yaml`, and `loadbalancer.yaml`. Keep the Service names and node port 30080.
3. Apply them with `sh run.sh`.
4. Test all three paths using the commands in Understand. The LoadBalancer test must return a real Dispatch response.
5. Choose **Check work**.
