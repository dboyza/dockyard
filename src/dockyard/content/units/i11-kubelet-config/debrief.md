## Compare your diagnosis

The worker's kubelet configuration had `shutdownGracePeriod: invalid-duration`.
That is not a length of time, so the kubelet refused to start, and the node stopped reporting.
The kubelet's journal named the field and the parse error directly.
Setting a valid duration, such as `0s`, and restarting the kubelet brought the same node back to `Ready`.

Check your understanding:
Why did the node show `NotReady` even though some of its containers were still running?
Why would deleting and rejoining the node have been a bigger change than the problem needed?
How could someone test a kubelet configuration change on one node before rolling it out to all of them?
