# Diagnostic approach

Service discovery and backend selection are different observations.
A DNS answer can correctly identify a Service whose selector matches no Pods.
For example, a Service selecting `app: catalog` and `tier: public` ignores an otherwise healthy Pod that only has `app: catalog`.
Every selector entry must match.
Inspect the EndpointSlices associated with the Service, then compare the selector with the ready workload labels.
A direct Pod request helps separate a selector failure from an application failure; it does not itself prove that the Service path has recovered.
