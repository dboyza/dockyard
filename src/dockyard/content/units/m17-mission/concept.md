# Restrict access while preserving the useful path

A working secure deployment must allow the intended workflow and deny specific unintended operations.
An unavailable application with every connection blocked is not a successful security outcome.
Treat the Kubernetes API identity, Pod network, admission boundary, and process privileges as separate controls and verify each with both positive and negative evidence.

The checkpoint supplies two nodes, known application dependencies, three distinguishable clients, and an independent egress target.
Use those controls to explain why a denied request is actually denied rather than misconfigured or unreachable for everyone.
Keep database credentials separate from service-account tokens and source control.

A useful security handoff names the protected resource, allowed identity or peer, denied alternative, observed result, and any remaining limitation.
For example, denying a frontend's direct database connection complements the API boundary but does not prove the API itself authorizes every business action.
The final note is a self-review artifact; automatic completion comes from observed access boundaries and a completed Dispatch job.
