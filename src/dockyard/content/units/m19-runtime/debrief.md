# Debrief: Trace a workload from CRI to its Linux cgroup

The CRI client observes the actual container runtime and the application process inside its Linux cgroup.
This connects a workload to host process supervision instead of inferring runtime health from a Kubernetes object alone.

## Explain your result

Which observation established the process identity, and how did the fresh persisted job extend that evidence beyond a process listing?

## Transfer beyond this lab

On a real node, keep runtime inspection bounded and preserve other workloads while distinguishing a runtime fault from an application failure.
