# Debrief: Apply deliberate changes in the right context

A valid apps/v1 declaration expresses the state that a controller should maintain, but API acceptance does not prove application availability.
The live release, owned replicas, and request through Service DNS connect that declaration to observed behavior.

## Explain your result

Explain why changing a manifest in your workspace without applying it leaves the cluster unchanged, and why applying it to another context would be dangerous.

## Transfer beyond this lab

For shared environments, review changes and compare intended state with the live object before applying a declaration.
