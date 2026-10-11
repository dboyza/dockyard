## What changed

The worker's kubelet now rejects requests without credentials and asks the API server to authorize the rest, so reaching port 10250 no longer means controlling the node's Pods.
The API server runs without profiling, so `/debug/pprof` is gone.
kube-bench confirmed the settings, and the live kubelet configuration and the API server's own responses confirmed the processes adopted them.

Check your understanding: why did kube-bench need `--benchmark cis-1.12`, and what would you check before trusting an older benchmark on a newer cluster?
Why is editing a static Pod manifest enough to change the API server, while the kubelet needs a restart?
