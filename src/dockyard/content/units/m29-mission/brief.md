## Release Dispatch 2.0 to production

Requirements:

- **Minimal image**: production runs an image with no shell, no `apk` or `pip`, no setuid or setgid files, and a non-root user, built from this workspace's `Dockerfile`.
- **Published and signed**: the image is in the release registry, and production runs it by digest, signed so that `cosign.pub` in your workspace verifies it.
- **Analysed**: KubeLinter reports no errors for the rendered `production.yaml`, and kubesec scores its Deployment at least 10 with no critical findings.
- **Admission**: `production` admits only images from the release registry pinned by digest.

Dispatch in `dispatch` must keep processing jobs.

Write `release-report.md` describing what shipped, the evidence for each requirement, and the risks that remain.
Then compare it with `report-rubric.md`.
