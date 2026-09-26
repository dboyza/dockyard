# Interpret an image scan as evidence

An SBOM inventories the components present in an artifact.
A vulnerability report joins that inventory to a dated advisory database.
Neither proves that an application is exploitable, nor that an image with no listed findings is safe.
Reachability, privileges, exposure, mitigations, and the age and coverage of the database matter.

This checkpoint intentionally installs unused PyJWT 1.7.1 as a known vulnerable teaching dependency.
Dispatch does not import it or accept JWTs.
The pinned Trivy database identifies CVE-2022-29217 in that component.
Removing an unused component reduces the exposed dependency set without replacing the supplied application.
Other base-image findings remain visible and require separate triage; this exercise does not claim a fully clean image.

The scanner uses a verified local executable and fixed database snapshot.
Preparation downloads them once; the scan itself disables updates and network lookups.
The database date is part of the evidence because a later advisory snapshot can produce different results for identical bytes.
A pinned snapshot makes the lesson repeatable, but production scanning should use a deliberate update policy.

For an unrelated service, a typical inspection might be:

```sh
trivy image --scanners vuln --format json --output findings.json report-service:5
trivy image --format cyclonedx --output inventory.json report-service:5
```

Our scan.py helper adds offline flags, saves a platform-specific image archive, and records its configuration digest alongside the reports.
The archive stays in the lab's private data directory, outside the editable workspace.
A registry manifest, an OCI index, and an image configuration are different objects with different digests.
Comparing hashes from different objects is not an integrity check.

Read scan-before.json and sbom-before.json before editing build.json.
The fixture is supplied through a named build context, so the main .dockerignore cannot accidentally include private lab data.
Set include_legacy_dependency to false, build and load the image, and replace the running API and worker Pods.
A new tag value alone does not replace existing containers.
Then record the after reports with the same database.

The checker independently scans the current image and inspects the running Python processes.
It accepts other valid ways to remove this unused dependency when the resulting artifact, reports, and actual workload agree.
Review the remaining findings instead of treating the exercise's passing result as a blanket security certification.
