## Keep frontend Pods away from the nodes

Pods in the `frontend` namespace can read each node's metadata credential and connect to every kubelet.

1. Fetch the practice credential from `untrusted-client` to see the exposure.
2. Rewrite `frontend-egress.yaml` so frontend Pods may reach only CoreDNS and the Dispatch API.
3. Apply it, confirm both clients can no longer reach `169.254.169.254` or port 10250 on either node, and choose **Check work**.

The trusted client must still submit jobs to Dispatch.
In your notes, explain why an allowlist of destinations is safer than blocking the metadata address alone.
