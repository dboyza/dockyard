## Investigate an intrusion

An alert from a partner says something in this cluster is behaving strangely: starting shells, reading Secrets it should not need, and probing the network.
Your job is to find what it is, stop it doing harm, and keep enough evidence to work out how it got there.

Use what this module taught.
Use Falco to see what processes do, and audit logs to see what identities do through the API.
Use immutable, restricted workloads as the standard to compare against.
Containment is not deletion.
Cut the workload off from the cluster and remove its access, but keep it running so it can be examined.

## Working on your own

Try it without hints first.
Hints and the reference solution are available, but using them marks this attempt as practice with help.
Check work tests the live cluster; your report is for your own review against `report-rubric.md`.
