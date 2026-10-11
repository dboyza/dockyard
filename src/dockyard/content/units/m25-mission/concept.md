## Bring a cluster to the agreed baseline

The security team has agreed a baseline that this cluster must meet before it goes into service, and a review has found it falls short in three areas.
Bringing it up to the baseline is your job, from finding the problems to proving they are fixed.

Use what this module taught: kube-bench for the node settings, egress NetworkPolicy for what Pods can reach, and checksums for anything staged for installation.
The specifics differ from the lessons, so read the evidence before you change anything.

Plan how you will prove each fix on the running system, not just in the file you edited.
The kubelet reports its live configuration through `configz`, control-plane Pods show their running flags, and connection attempts from a client Pod show what the network really allows.

## Working on your own

Try it without hints first.
Hints and the reference solution are available, but using them marks this attempt as practice with help.
Check work tests the live cluster; your report is for your own review against `report-rubric.md`.
