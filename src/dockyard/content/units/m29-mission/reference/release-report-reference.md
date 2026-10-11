# Release report

## What shipped

Dispatch 2.0, built from the checkpoint Dockerfile with a final step that clears setuid bits and removes BusyBox with its shells, apk, and pip, published to the release registry, and signed by digest with the team's cosign key.

## Evidence

- `cosign verify` succeeds for the deployed digest with `cosign.pub`.
- A container from the image has no shell, package manager, or setuid file, and runs as user 10001.
- KubeLinter reports no errors for `production.yaml`, and kubesec scores the Deployment 14 with no critical findings.
- In `production`, the admission policy refuses images from other registries and images referenced by tag.

## Remaining risks

- The admission policy does not verify signatures itself; a signature-verifying admission controller would.
- Signatures were not recorded in a transparency log, because the lab is offline.
