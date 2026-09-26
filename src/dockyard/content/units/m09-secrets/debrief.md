# Follow configuration into the process

Trace the source object, Pod reference, delivery mechanism, and application read that establish each configured value.
Explain which changes require a rollout and which require the application to reread a projected file.
Describe one way a credential could still be exposed despite being stored as a Secret.

For identity, distinguish a successful administrator request from a successful request carrying the workload's own token.
Explain why an allowed Pod list and denied Secret list provide different evidence from merely seeing a RoleBinding object.
Before calling the environments isolated, state exactly which boundary was demonstrated and which boundaries still require network and storage controls.
