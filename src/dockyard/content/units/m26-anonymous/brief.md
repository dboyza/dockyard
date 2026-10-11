## Stop anonymous callers reading the cluster

Anyone who can reach this API server can read Pods and ConfigMaps without credentials.

1. Confirm it with an unauthenticated `curl` request, then find and delete the binding responsible and its ClusterRole.
2. Create `/etc/kubernetes/auth-config.yaml` on the control-plane node so anonymous requests are accepted only for `/livez`, `/readyz`, and `/healthz`.
3. Pass it to the API server with `--authentication-config`, mounting the file into the static Pod.
4. Confirm the private request now returns 401 while `/readyz` still answers, and choose **Check work**.

Dispatch must keep processing jobs.
In your notes, explain the difference between a 401 and a 403 response, and which one each of your two fixes produces on its own.
