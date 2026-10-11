# Access requirements

Agreed with each team during the security review.

## CI deployer

- Identity: the ServiceAccount `deployer` in the `ci` namespace.
- Needs: read Deployments in `dispatch` and change their images, which means `get`, `list`, `watch`, `patch`, and `update` on `deployments` in the `apps` API group.
- Nothing outside the `dispatch` namespace, and no access to Secrets.

## Dispatch operators

- Identity: anyone in the group `dispatch-operators`.
- Needs: read everything in `dispatch` except Secrets, including Pod logs, to investigate incidents.
- No changes to anything, and nothing outside `dispatch`.
