## The capstone

This is the last mission of the course, and it brings together what you have learned about clusters, workloads, and operations.

Dispatch runs on a cluster with **three control-plane nodes and one worker**.
The first control-plane node has lost its API server and its etcd member.
They must **stay stopped**.
The point is to show the cluster keeps working while one of its three control-plane nodes is down.
Do not restart them, remove the etcd member, or rebuild the cluster.

Since the outage, several other things have gone wrong:

- kubectl cannot reach the cluster through its usual address;
- users say Dispatch does not work;
- the API is running fewer copies than agreed;
- the inventory tool has more access than it needs.

## The design to restore

- The cluster's API address is the load balancer on the worker, which should send traffic to the control-plane nodes that are actually running. The high availability lesson in module 20 showed how to check and regenerate its configuration.
- The two surviving etcd members keep quorum, and all three memberships stay registered.
- The Dispatch Service sends requests to the stable API Pods, and at least one worker processes jobs.
- The API meets the budget from the decisions lesson.
  It runs 2 to 4 copies, with total requests of at most 1 CPU and 512 MiB, and total memory limits of at most 1 GiB.
  A PDB named `dispatch-operations` covers `app: dispatch, track: stable` and keeps at least one copy available.
- `dispatch-reader` can list Pods in `dispatch` and nothing more.

## Ship the handoff release

Finally, release a new version of Dispatch:

1. Put `dispatch-handoff-v1` in the workspace's `VERSION` file.
2. Run `python build.py`. It builds the image with Docker and copies it into every VM.
3. The image name does not change, so restart both Deployments to pick up the new build: `kubectl rollout restart deployment/dispatch deployment/worker`, then wait for both rollouts.

Check work asks each running API and worker Pod which version it has, so editing the file without rebuilding and restarting is not enough.

## Working on your own

Try it without hints first.
Hints and the reference solution are available, but using them marks this attempt as practice with help.
Test each layer before you change it, and fix what the evidence shows.

## Your handoff

In `handoff.md`, write for the next person on call:

- each symptom and the observation that explained it;
- the order you fixed things in;
- commands to check the final state, with what each should show;
- what this cluster can now survive, and what it still cannot: the single worker, the database's local volume, and the load balancer running on that same worker;
- when to escalate, for example if a second control-plane node fails.

Keep credentials, kubeconfigs, and snapshot data out of it.
Check work tests the cluster; the handoff is for you to compare with the debrief.
