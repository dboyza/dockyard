## What changed

The resizer no longer runs privileged with the node's filesystem mounted inside it.
It runs as a non-root user with no capabilities, a read-only root filesystem, resource limits, and no API token.
Both analysers pass the manifest that is actually deployed.

Check your understanding: where in a delivery pipeline would you run these tools, and what should happen when one fails?
Why does a high kubesec score not prove a workload is secure?
