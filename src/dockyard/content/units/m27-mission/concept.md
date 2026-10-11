## Confine a workload that must keep working

A customer-facing renderer turns uploaded templates into report pages.
It parses untrusted input, its vendor image must run as root, and today nothing confines it.
The control plane it shares a cluster with also carries leftovers from an old debugging session.

Your job is to shrink the attack surface and confine the renderer, without stopping it from producing pages.
Use what this module taught: surveying a node's services, ports, and accounts; AppArmor profiles loaded on every node; and seccomp profiles.

## Working on your own

Try it without hints first.
Hints and the reference solution are available, but using them marks this attempt as practice with help.
Check work tests the live cluster; your report is for your own review against `report-rubric.md`.
