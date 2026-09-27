# Debrief: Scale from measurements and bound disruption

The autoscaler depends on a functioning metrics path and meaningful workload resource requests.
A changing replica count is useful evidence only when it corresponds to the observed demand and stays within the declared bounds.

## Explain your result

Why would adding replicas fail to help a bottleneck in a shared database or a queue consumer with an invalid configuration?

## Transfer beyond this lab

Measure scale-up delay, stabilization, and downstream capacity before relying on autoscaling during production bursts.
