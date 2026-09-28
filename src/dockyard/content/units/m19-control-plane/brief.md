## Fix the operator client inside the control-plane VM

`$HOME/.kube/operator.conf` inside the control-plane VM cannot reach the cluster, although your lab terminal can.

1. From your lab terminal, run `kubectl get nodes`.
2. Enter the control plane and try `kubectl --kubeconfig="$HOME/.kube/operator.conf" --request-timeout=5s get nodes`, and read the error category.
3. See which server it targets, without printing credentials: `kubectl --kubeconfig="$HOME/.kube/operator.conf" config view -o jsonpath='{.clusters[0].cluster.server}'`.
4. Check the static components with `sudo crictl ps`, and repair the operator client so it lists both nodes. Keep the file private, mode 600.
5. Exit and choose **Check work**.

Do not turn off certificate verification, change your computer’s own kubeconfig, or replace healthy control-plane components.
In your notes, explain why your lab terminal worked while the operator client failed.
