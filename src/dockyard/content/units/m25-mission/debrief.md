## What changed

The worker's kubelet no longer serves its unauthenticated read-only API, and the controller manager runs without profiling.
The frontend egress policy is now an allowlist, so the kubelet ports that the old metadata-only exception left open are closed too.
The altered `kubeadm` is gone from the staging folder, and the genuine binaries remain.

Check your understanding: the original egress policy did block the metadata address.
What does that show about writing policies as exceptions?
Which of your fixes would a fresh kube-bench run not have caught at all?
