## Isolate an untrusted workload

A partner integration is about to go live: `plugin-runner` runs code that partners upload, and it holds credentials for a partner's API.
The security team will approve it only if three layers of isolation are in place, and setting them up is your job.

Use what this module taught: encryption at rest for Secrets, a gVisor sandbox chosen through a RuntimeClass, and WireGuard between the nodes.
Plan the order: some steps restart the API server or containerd, and each should be checked before the next.

## Working on your own

Try it without hints first.
Hints and the reference solution are available, but using them marks this attempt as practice with help.
Check work tests the live cluster; your report is for your own review against `report-rubric.md`.
