# One application, several workload lifecycles

The Dispatch checkpoint now includes a long-running API, independently scalable queue workers, a node observer, and finite database maintenance.
Each controller expresses a different operational intent.
A green Pod list alone does not show that submitted work is processed or that maintenance reaches its durable effect.
Use evidence tied to those application outcomes.

This module deliberately retains an ephemeral database volume.
Document that limitation and identify the next storage change before describing this stack as production ready.
