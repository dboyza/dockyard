# Publication follows a successful candidate test

A delivery pipeline is a repeatable sequence with explicit failure gates.
The supplied pipeline builds the Dispatch image, runs real HTTP contract tests inside that image, publishes it to the app-owned registry, and records the registry's content digest.
A nonzero test exit must stop publication.
A successful build alone proves neither API behavior nor dependency readiness.
These fast contract tests cover the health response and invalid-request rejection; the final cluster check separately exercises a real database-backed job.

```sh
python -m json.tool pipeline.json
python pipeline.py
python -m json.tool release.json
```

The pipeline script uses subprocess exit status to stop on a failed build, test, or push.
Its run_tests setting is deliberately visible so you can diagnose an accidentally bypassed gate.
The test container has no external network and runs as the image's non-root user.
The HTTP server binds its own loopback interface inside that container.

For a different service, a minimal shell gate would look like this:

```sh
set -eu
docker build -t report-service:candidate .
docker run --rm --network=none report-service:candidate python -m unittest
docker tag report-service:candidate "$PRIVATE_REGISTRY/report-service:reviewed"
docker push "$PRIVATE_REGISTRY/report-service:reviewed"
```

The assignment keeps its supplied tests and repairs the gate, rather than changing what a passing test means.
The checker independently runs the packaged HTTP tests against the actual published image and compares the recorded source hashes with the current build inputs.
A tag is a convenient name for publication, while the resulting digest is the immutable deployment input.
Local pipeline records are useful reproducibility evidence, not signed supply-chain attestations.

The registry accepts unauthenticated HTTP on an assigned loopback port and the owned Docker bridge.
This is a local learning compromise, not a production registry configuration.
The lab changes containerd mirror files only inside its owned cluster nodes.
It does not change Docker Desktop trust settings or send an image to an external registry.

The pipeline labels each published artifact with its release version and lab identity.
This records release provenance and gives the published image a distinct configuration identity from the locally imported practice image.
Kubernetes 1.35 verifies access to previously pulled images by identity and repository; importing one alias does not authorize every alias of an image pulled elsewhere.
The lab preserves that credential verification behavior.
