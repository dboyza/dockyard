Initialize the primary guest using Kubernetes 1.35.8 and Pod subnet `10.244.0.0/16`.
The API readiness endpoint must respond through the guest's kubeadm administrative client, and all four static components must run.
Refresh the private host client and inspect the resulting node.
Leave worker join and CNI installation for the following lesson.

Use the configuration inspection and initialization workflow in the concept page.
Record why a responsive API does not yet imply that ordinary Pods can communicate.
