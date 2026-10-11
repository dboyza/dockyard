## What changed

Production now runs a minimal image built from your Dockerfile, published to the release registry, signed by digest, and deployed from a manifest both analysers accept.
The admission rule means the next release has to arrive the same way: from the release registry, pinned by digest.

Check your understanding: list each check this release passed, and the kind of attack or mistake each one stops.
Which single additional control would most improve this pipeline, and why?
