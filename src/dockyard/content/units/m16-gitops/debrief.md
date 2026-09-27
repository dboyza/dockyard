# Debrief: Reconcile a local Git declaration

The reconciler reads the declared state from the local Git source and applies it to the owned cluster.
Changing a live object directly can therefore be temporary when the committed declaration still requests something else.

## Explain your result

Trace a commit through source retrieval, reconciliation, and the resulting workload, identifying where each status is observed.

## Transfer beyond this lab

Protect repository write access as deployment authority and keep secrets out of committed application declarations.
