## The host and container platforms are different facts

This Mac uses an ARM64 processor, while Docker Desktop runs a Linux VM for Linux containers.
The native application image in this lab should therefore report linux/arm64, not darwin/arm64.
An amd64 image may require emulation here, which can affect performance and compatibility.
Inspect the artifact you actually built rather than inferring its architecture from a tag name.

```sh
docker image inspect --format '{{.Os}}/{{.Architecture}}' "$DOCKYARD_IMAGE"
```

A multi-platform image reference can point to an index containing platform-specific manifests.
The runtime selects a matching platform, and each platform's content can have its own digest.
Building a tested native image is sufficient for this exercise; it does not certify that an untested amd64 variant works.

## Context control is a supply-chain boundary

A broad COPY can accidentally include local credentials, Git metadata, or debugging artifacts.
Deleting a copied secret in a later layer does not remove it from earlier image layers.
The correct preventive boundary is to keep unwanted files out of the build context or copy only explicit required files.
Build-time secrets that are genuinely needed should use an appropriate secret mount, not a persistent build argument or copied file.

## Worked example: exclude local material

```dockerignore
.env
*.key
.git
__pycache__
```

The task includes a deliberately fake .env file so you can observe this boundary safely.
It contains no real credential and must never be replaced with one.
The checker examines all layers of the final image archive for the forbidden file, so a later RUN rm is not an acceptable repair.

## What a digest does and does not establish

A digest identifies content; it does not establish who authored it or whether it contains vulnerabilities.
Provenance, signatures, SBOMs, and vulnerability findings answer different questions.
The advanced hardening module will use scanning and SBOM evidence in more depth.
For now, combine precise artifact identity with deliberate inputs and an actually tested native runtime.
