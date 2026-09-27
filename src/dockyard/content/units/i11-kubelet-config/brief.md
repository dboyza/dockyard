# Incident report

A worker stopped reporting Ready shortly after a kubelet configuration edit.
The API and control-plane processes remain available.
Restore the original worker's agent and readiness without resetting or rejoining it.
Preserve both node UIDs, the namespace, sentinel, and stored application data.
Demonstrate fresh scheduling and a completed Dispatch job after the node reports Ready.

Use the guest journal and configuration as evidence.
Record the invalid field and why a process restart without a configuration repair would repeat the failure.
The debrief is a self-review rubric.
