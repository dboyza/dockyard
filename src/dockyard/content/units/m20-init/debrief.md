## A control plane, but not yet a working cluster

kubeadm created the certificates, the static control-plane Pods, and the administrator credentials, and the API answers.
There is still no Pod network and only one node, so nothing useful can run yet.

Check your understanding:
Which four components does the kubelet now run from `/etc/kubernetes/manifests`?
Why is the node NotReady, and what will fix it?
