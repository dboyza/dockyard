# Diagnostic approach

A process can be restarted because it exits, fails a liveness probe, or exceeds a resource limit.
These causes require different repairs.
Read the previous termination reason and events before treating every restart as a probe problem.
For a separate example, a cache that holds 40 MiB needs room for the interpreter, connections, and temporary allocations as well.
A memory request affects scheduling; a memory limit constrains the container at runtime.
Increase a limit only after relating the observed workload to an explicit budget.
This supplied worker deliberately retains a bounded 80 MiB working set so the failure and recovery are observable without exhausting the host.
