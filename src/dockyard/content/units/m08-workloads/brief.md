## Get the workers and the node agent running

1. Look at the `worker` Deployment and the `dispatch-node-agent` DaemonSet and work out why each has no Pods.
2. Change `worker.yaml` to ask for two copies.
3. Remove the impossible `dockyard.invalid/node: missing` node selector from `agent.yaml`.
4. Apply both files and wait for both rollouts.
5. Submit a job and find a worker’s log line showing it was completed.
6. Choose **Check work**.

Check work submits its own job and checks a worker finishes it, and that the agent is running on every node it is allowed on.
