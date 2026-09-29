# Operating handoff

## Symptom and evidence

- The API had been scaled to 1 copy.
- `kubectl auth can-i get secrets --as=system:serviceaccount:dispatch:dispatch-reader` returned `yes`; the Role allowed every verb on every resource.

## Repair and verification

- Scaled the API to 2 copies: 50m CPU and 64 MiB requested, 384 MiB of memory limits, all within the budget.
- Created the `dispatch-operations` PDB for `app=dispatch,track=stable` with `minAvailable: 1`; it allows 1 disruption.
- Restored the Role from `identity.yaml`; the account can list Pods and is refused Secrets, Deployment changes, and RoleBindings.
- A new job completed, and the job stored before the change is still there.

## Recovery boundaries and next actions

Two API copies help during rollouts and Pod crashes, but both run on the single worker next to the database's volume, so losing that node still stops Dispatch.
Find out why the Role was widened, and whether its token could have been used in the meantime.
