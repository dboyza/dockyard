## Create the control plane

1. Inspect the VM’s runtime and generate `init.yaml` as shown in Understand. Check it uses Kubernetes 1.35.8 and Pod subnet `10.244.0.0/16`.
2. Run `kubeadm init` inside the control-plane VM with that file.
3. Run `python -m dockyard.native refresh-client`, then `kubectl get nodes` and `kubectl get pods -n kube-system`.
4. Choose **Check work**.

Do not join the worker or install networking yet; that is the next lesson.
In your notes, explain why the API answering does not mean Pods can talk to each other yet.
