# Incident report

## Detection

Falco, with a rule for shells in application containers, reported `storefront/catalog` starting a shell every 20 seconds.

## Investigation

- `catalog` runs as the ServiceAccount `storefront/catalog`, which the RoleBinding `catalog-support` allowed to get and list Secrets in `dispatch`.
- The Pod also tried to reach the instance metadata address every cycle.

## Containment

- Deleted the RoleBinding `catalog-support`; the ServiceAccount can no longer read Secrets in `dispatch`.
- Applied `quarantine-catalog`, a NetworkPolicy with no rules for the `catalog` Pods, so they can send and receive nothing.
- Kept the Pod running for examination instead of deleting it.

## Next steps

- Rotate the `dispatch-database` password, because it may have been read.
- Use the audit log, once enabled, to find when `catalog-support` was created and by whom.
- Rebuild `catalog` from a trusted image before returning it to service.
