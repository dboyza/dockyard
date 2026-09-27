# Separate node health from workload process health

A running application container can outlive an unhealthy node agent.
The API may remain available while the affected kubelet stops renewing the node status.
Read the Node conditions and the host service journal before resetting or replacing a node.
For a separate example, a field expecting a duration such as `15s` cannot interpret a descriptive word as a duration.
The host journal can identify a configuration parse failure that application logs cannot explain.
A kubelet restart only helps once the configuration it reads is valid.
