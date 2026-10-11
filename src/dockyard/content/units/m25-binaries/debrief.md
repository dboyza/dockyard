## What changed

The staged `kubectl` had been altered: it still ran and printed its usual version, but its SHA-512 checksum did not match the official release, so it is gone.
`kubeadm` and `kubelet` matched exactly and stay ready for the maintenance window.

Check your understanding: why must the checksums come from the official release site rather than a file next to the binaries?
How does an image digest give a Deployment the same guarantee for container images?
