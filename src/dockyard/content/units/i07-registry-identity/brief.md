# Incident report

The release was published successfully, but newly created API Pods cannot retrieve it after a credential rotation.
Inspect the pull events and repair the workload's registry identity.
The registry authority is in `registry.txt`; its current local username is `learner` and the password is supplied in the lab-only `DOCKYARD_REGISTRY_PASSWORD` environment variable.
Do not paste the password into a runbook or shell command argument.
A program can construct the Secret in memory and send it to kubectl over standard input.

Retain registry authentication and the published `dispatch:incident` release.
Restore two ready API replicas with imagePullPolicy Always and complete a fresh persisted job.
Keep the namespace, original database claim, and stored job.
The validator launches a separate short-lived Pod using the workload pull identity and checks its actual execution.
Preloading a local image, disabling authentication, or switching back to the non-registry image does not meet this contract.

Record how you distinguished an absent image, an unreachable registry, and a rejected credential.
Use the debrief as a self-review rubric.
