## Detect shells in application containers with Falco

Falco is installed on the worker but not running, and nobody has written rules for this cluster's applications.

1. Write a Falco rule in `/etc/falco/rules.d/dockyard.yaml` on the worker that alerts when a shell starts in a container in the `billing`, `dispatch`, or `frontend` namespaces, naming the namespace and Pod.
2. Validate it, then run Falco as a service that also starts at boot.
3. Use the alerts to find which workload keeps starting shells, and write it into `finding.txt` as `NAMESPACE/NAME`.
4. Choose **Check work**.

In your notes, explain why detection is still needed when Pods already run with restricted security settings.
