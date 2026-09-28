## Your own maintenance window

The team has approved upgrading this cluster from 1.34.12 to 1.35.8, and it is your job from start to finish: plan it, carry it out, check it, and hand it over.
Dispatch is running on it, and its data must survive.

Before you start, decide what you will check after each step, and what would make you stop.
Keep the stages separate in your mind: staging packages, installing kubeadm, upgrading the control plane, draining and upgrading each node’s kubelet, and returning each node to service.

With one control-plane node and the database on the worker, there will be real interruptions.
Say so honestly in your handoff instead of claiming the service never stopped.

## Working on your own

Try it without hints first.
Hints and the reference solution are available, but using them marks this attempt as practice with help.
Check work tests the live cluster; your handoff is for your own review against `handoff-rubric.md`.
