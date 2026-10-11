## Verify the staged binaries before anyone installs them

Three Kubernetes binaries wait in `/opt/dockyard/staged` on the control-plane node for the next maintenance window.

1. Compare each one with its official SHA-512 checksum from `release-checksums`, using `sha512sum -c`.
2. Delete any staged binary that does not match.
3. Keep the binaries that match, and choose **Check work**.

Leave the installed binaries in `/usr/bin` untouched.
In your notes, explain why running the suspect binary with `version` would not have revealed the problem.
