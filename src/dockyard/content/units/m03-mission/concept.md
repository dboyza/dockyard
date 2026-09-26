## A small service boundary

Dispatch now has an internal HTTP dependency.
Your job is to provide a stable communication path and a single host-facing API endpoint.
The supplied image checkpoint can run in both roles, and the dependency response includes the identity of the process that answered.
That lets you prove the API reached its actual peer rather than merely receiving an unrelated success response.

This independent mission begins with source files only.
Use the earlier build, process, and network skills to create the required topology.
Keep the dependency off host-published ports and use its network alias rather than an observed IP address.
