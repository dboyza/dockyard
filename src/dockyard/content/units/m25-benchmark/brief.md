## Fix three benchmark findings

A security review ran kube-bench against this cluster and reported three failures that must be fixed before the cluster goes into service.

1. Confirm the findings: checks 4.2.1 and 4.2.2 on the worker, and check 1.2.15 on the control plane.
2. Make the worker's kubelet refuse anonymous requests and authorize the rest through the API server, then restart it.
3. Turn off API server profiling in its static Pod manifest, and wait for the API to return.
4. Run kube-bench again, confirm all three checks pass, and choose **Check work**.

Change only these settings; Dispatch must keep processing jobs.
In your notes, explain why anonymous access combined with `AlwaysAllow` was dangerous even though port 10250 is not published outside the cluster.
