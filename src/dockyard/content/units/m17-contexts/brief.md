# Match admission intent with a restricted process

The namespace enforces only Baseline, and the API allows privilege escalation, retains CHOWN, and has a writable root filesystem.
Repair admission.yaml and the API template in platform.yaml without changing the supplied application behavior.
Apply the files and wait for the rollout; a namespace label alone does not replace existing Pods.
Keep the documented writable volumes and non-root identities for dependencies.
Verify rejected escalation at admission, actual kernel-level process restrictions, and successful job completion.
