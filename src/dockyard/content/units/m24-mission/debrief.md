## Compare your recovery

The load balancer was sending API traffic only to the stopped control-plane node.
Regenerating its configuration with `python -m dockyard.native lb-config` listed all three control-plane nodes; HAProxy's health checks then skipped the stopped one and sent traffic to the two that were running, while their etcd members kept quorum.
The application had the faults from the triage lesson, a Service selecting `track: retired` and the worker scaled to zero, plus the decisions lesson's single API copy and wide-open Role.
The release step showed the difference between changing a file and running a new build.

Your order may differ, but the load balancer usually comes first, because nothing else can be changed until kubectl reaches the API.

## Check your understanding

- Why could the cluster accept changes with one of three etcd members down, and what would happen if a second failed?
- Which parts of this system are still single points of failure?
- If you rolled back the release, what would and would not go back to how it was?

## Beyond this lab

You have now built, broken, and repaired a real Kubernetes cluster from the node up.
The course's practice exams are the next step: timed tasks in the style of the CKA and CKAD.
