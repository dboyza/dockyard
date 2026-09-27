# Debrief: Extend the API with a reconciled WorkerPool

A custom resource extends the API vocabulary, and a running controller is responsible for reconciling that declared intent.
The WorkerPool object alone cannot create useful workers without the corresponding controller and its required authority.

## Explain your result

Trace one change from the custom resource to the managed workload and explain how status differs from the requested specification.

## Transfer beyond this lab

Production operators need bounded privileges, repeatable reconciliation, and failure reporting that survives retries.
