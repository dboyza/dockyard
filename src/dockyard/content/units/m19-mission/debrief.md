# Debrief: Mission: recover the native supervision chain

The native recovery combines CRI process visibility, fresh kubelet communication, valid client access, and a persisted application transaction.
Each layer can appear healthy while a neighboring layer remains broken, which is why the final job is a separate check.

## Explain your result

Reconstruct the supervision chain from Linux service to runtime process to node lease to application result, naming the fault you repaired at each boundary.

## Transfer beyond this lab

A native node exposes host-level repair options that are hidden by an application-only cluster, but those options require tighter targeting and operational care.
