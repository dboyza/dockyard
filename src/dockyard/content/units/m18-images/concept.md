## What is inside your image?

An image contains far more than your own code: an operating system’s packages, a language runtime, and libraries.
Any of them can have known security flaws.
Two tools help you see them:

- A **software bill of materials (SBOM)** lists the components in an image.
- A **vulnerability scanner** compares that list with a database of published problems, identified by **CVE** numbers, and reports matches.

Treat the results as evidence, not a verdict.
A reported flaw only matters if the vulnerable code can actually be reached and exploited in how you run it.
And an image with no findings is not proven safe: the database only knows about problems published so far.
That is why the database’s date belongs in every report: the same image scanned against a newer database can show new findings.

## This lab

This version of Dispatch deliberately installs an old library it never uses, PyJWT 1.7.1, which has a known flaw, CVE-2022-29217.
Dispatch does not import it, so the flaw is not reachable, but an unused component is still something that could be misused, and it adds noise to every scan.
Removing what you do not need is one of the simplest ways to reduce risk.

The lab uses the **Trivy** scanner with a fixed, downloaded database so results are repeatable.
For a different service, typical commands look like this:

```sh
trivy image --scanners vuln --format json --output findings.json report-service:5
trivy image --format cyclonedx --output inventory.json report-service:5
```

The supplied helpers wrap these for the lab, working offline:

- `python scan.py before` or `after` scans the current image and writes `scan-PHASE.json` (the findings), `sbom-PHASE.json` (the inventory), and `scan-evidence-PHASE.json`, which records the image’s identity and the vulnerability database’s date under `database.updated_at`.
- `build.json` has one setting, `include_legacy_dependency`, which controls whether the old library is installed.
- `sh repair-image.sh` rebuilds the image, restarts the API and worker so they run the new image, and scans again as `after`.

Restarting matters: building a new image changes nothing that is already running.

## Reading the results

Look in `scan-before.json` for CVE-2022-29217 and the package it belongs to, and find PyJWT in `sbom-before.json`.
After the rebuild, it should be gone from both.
Other findings in the base image will remain.
They are real and deserve review, but they are not this lesson’s task, so a pass here is not a clean bill of health for the whole image.

Also note that an image has several different fingerprints: the registry manifest, a multi-platform index, and the image configuration each have their own digest.
Comparing digests of different kinds of object tells you nothing.
