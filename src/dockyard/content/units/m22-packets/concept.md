## Readiness is not a packet trace

Both nodes can remain Ready while packets between their Pods are dropped.
Kubelet heartbeats use the node network to reach the API, while this Calico profile carries cross-node Pod packets inside VXLAN over UDP port 4789.
Those paths have different addresses, protocols, and failure points.
The node network is `192.168.104.0/24`; Pod addresses come from `10.244.0.0/16`.
Keep the ranges separate when interpreting routes.

Dispatch API and database workloads run on the worker.
The trusted frontend client runs on the control plane, so its requests cross the guest boundary.
The browser's endpoint terminates on the worker and can appear healthy while that separate frontend path fails.
A successful local health request therefore cannot prove cross-node connectivity.

## Worked example: move from identity to the path

```sh
kubectl get nodes -o wide
kubectl get pods -n frontend -o wide
kubectl get pods -l app=dispatch -o wide
limactl shell --workdir=/tmp "$DOCKYARD_CONTROL_PLANE" ip -d link show vxlan.calico
limactl shell --workdir=/tmp "$DOCKYARD_CONTROL_PLANE" sudo iptables -t raw -nvL PREROUTING --line-numbers
```

Identify the frontend node, destination Pod IP, and underlying worker address before interpreting a counter.
A direct HTTP request to the destination Pod IP removes DNS and Service translation from that particular test.
A request to the Service name adds both those dependencies back.
Use `/healthz` for process reachability and `/readyz` or a fresh job for dependency readiness.
They answer different questions.

## The injected boundary

This fixture adds one raw-table PREROUTING rule on the control-plane guest that drops UDP destination port 4789.
This early hook observes the outer UDP packet before subsequent tunnel processing.
Its comment is `dockyard-$DOCKYARD_LAB-vxlan`.
The rule does not remove the Calico interface or stop kubelet, so resource status alone can be misleading.
Observe its packet counter while trying cross-node traffic and compare that evidence with the interface, route, and application observations.

Remove only the identified rule, using its exact match specification or a freshly inspected rule position.
Never flush the guest's entire firewall: Calico and Kubernetes depend on other rules in the same system.
For an exact deletion, use the same protocol, destination port, comment match, and DROP target with `iptables -t raw -D PREROUTING`.
The supplied lab identifiers keep the operation confined to this attempt's own guest and injected rule.

## Prove useful connectivity

The assessment reaches an actual API Pod IP from the trusted frontend on the other node.
It also creates a new diagnostic Service, resolves its fresh DNS name, and checks its new ClusterIP route.
Finally, the normal application path must complete and persist a new job while retaining the original state.
An interface existing or a policy object looking plausible is only supporting evidence, not the operational outcome.
