## Fix DNS and Service routing

1. Compare the CoreDNS Corefile with `Corefile.original`, fix the cluster domain, and restart CoreDNS.
2. Find why the new kube-proxy Pods cannot start, set the correct image, and wait for the rollout on both nodes.
3. Test a new Service: its name must resolve to its real ClusterIP, and that IP must reach an API Pod.
4. Choose **Check work**.

Dispatch must become fully ready again, keep its data, and complete a new job.
In your notes, explain why an old, working Service would not have proved kube-proxy was fixed.
