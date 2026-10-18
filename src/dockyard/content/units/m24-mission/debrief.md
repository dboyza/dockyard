## Compare your recovery

The load balancer was sending API traffic only to the stopped control-plane node.
Regenerating its configuration with `python -m dockyard.native lb-config` listed all three control-plane nodes.
HAProxy's health checks then skipped the stopped one and sent traffic to the two that were running.
Their etcd members kept quorum.
The application had the faults from the triage lesson: a Service selecting `track: retired` and the worker scaled to zero.
It also had the decisions lesson's faults: a single API copy and a wide-open Role.
The release step showed the difference between changing a file and running a new build.

Your order may differ, but the load balancer usually comes first, because nothing else can be changed until kubectl reaches the API.

## Check your understanding

- Why could the cluster accept changes with one of three etcd members down, and what would happen if a second failed?
- Which parts of this system are still single points of failure?
- If you rolled back the release, what would and would not go back to how it was?

## Beyond this lab

You have now built, broken, and repaired a real Kubernetes cluster from the node up.
Two paths follow from here.
The practice exams test you with timed tasks in the style of the CKA and CKAD.
Phase 5 hardens a cluster like this one against attack, and prepares you for the CKS.
