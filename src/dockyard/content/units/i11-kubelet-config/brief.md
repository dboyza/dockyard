## Get the worker Ready again

- Bring the worker's kubelet back so the node reports `Ready`.
- Keep the same nodes: do not delete, reset, or rejoin the worker.
- Keep the namespace, the `maintenance-sentinel` ConfigMap, and the database's data.
- After the node is Ready, show that a new Pod gets scheduled and a new Dispatch job completes.

In your notes, record the log line that pointed at the cause, the setting you changed, and why restarting the kubelet without changing it would fail again.
