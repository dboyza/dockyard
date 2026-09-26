The workspace VERSION says `incident-release-v2`, but a fresh container still reports `incident-release-v1` after a successful build.
The release script builds from a staged context directory used by an older packaging step.
Diagnose which files the builder actually receives and ship the current root application without bind-mounting it into the running container.
Prove the assigned endpoint serves the new built artifact.
