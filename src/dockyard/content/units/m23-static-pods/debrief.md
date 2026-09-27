# Debrief: Recover the reconciler and its static workload

The kubelet reconciles the static manifest into a running control-plane process without waiting for a Deployment controller.
A fresh scheduler assignment shows that scheduling recovered, whereas an old running Pod could survive while the scheduler remained unavailable.

## Explain your result

Which host observation identified the missing static workload, and which new API observation demonstrated that it was useful after restart?

## Transfer beyond this lab

When the API is unhealthy, preserve access to host service logs, runtime inspection, and the authoritative static manifests.
