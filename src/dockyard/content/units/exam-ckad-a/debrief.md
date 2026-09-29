## Reviewing your attempt

Open each task in the results to see what Dockyard checked and what it found.
A task can earn part of its marks when some of its checks pass.

Look for the gap between "it exists" and "it works":

- a new image is only useful once it is loaded into the cluster and the Pods restart on it;
- a ConfigMap change only reaches environment variables when the Pods restart;
- a Service with the wrong `targetPort` has no working endpoints, however healthy the Pods are;
- a NetworkPolicy is only proven when the allowed client connects *and* the other one is refused.

For each task you missed, work through the lesson it links to, then try a fresh attempt without help.
