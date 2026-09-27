# Debrief: Deliver configuration without rebuilding

The configuration object is only the beginning of the delivery path; the Pod reference and the application read determine the effective value.
Comparing the process setting with the mounted file exposes the difference between startup environment capture and projected file delivery.

## Explain your result

After editing a ConfigMap, which consumer needs a rollout, and which needs to reopen its configuration file?

## Transfer beyond this lab

Use application-level observations when planning configuration changes instead of assuming that an updated API object means every process has refreshed.
