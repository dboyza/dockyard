## Only publish what passed its tests

A **delivery pipeline** is an automated sequence that turns source code into something you can deploy: build it, test it, publish it.
The important word is **gate**: a failed step must stop everything after it.
A build that succeeds proves only that the image was assembled, not that the application inside works.

## This lab’s pipeline

`pipeline.py` does four things in order:

1. Builds the Dispatch image.
2. Runs real HTTP tests, `test_release.py`, inside that image. The test container has no network access and runs as the image’s ordinary user.
3. Pushes the image to this lab’s registry.
4. Records the registry’s **digest** for the image, plus fingerprints of the source files, in `release.json`.

Each step checks the previous one’s exit status and stops on failure.
But `pipeline.json` has a switch, `run_tests`, and it is currently `false`: the tests are skipped and anything that builds gets published.

```figure
pipeline-gate
```

```sh
cat pipeline.json
python pipeline.py
python -m json.tool release.json
```

The same idea in a plain shell script, for a different service, looks like this:

```sh
set -eu
docker build -t report-service:candidate .
docker run --rm --network=none report-service:candidate python -m unittest
docker tag report-service:candidate "$PRIVATE_REGISTRY/report-service:reviewed"
docker push "$PRIVATE_REGISTRY/report-service:reviewed"
```

`set -eu` makes the script stop at the first failing command, so a failing test means nothing gets pushed.

## Prove the gate really stops things

Do not just trust that the gate works; see it fail.
Copy the tests, break one assertion in the copy, and run both against the published image:

```sh
IMAGE=$(python -c "import json; print(json.load(open('release.json'))['image'])")
docker run --rm -i --network=none "$IMAGE" python - < test_release.py; echo "exit $?"
cp test_release.py broken_test.py
docker run --rm -i --network=none "$IMAGE" python - < broken_test.py; echo "exit $?"
rm broken_test.py
```

`python -` runs a script read from input, and `< file` supplies the file, so the tests run inside the image without copying anything into it.
Before the second run, edit `broken_test.py` so one `assertEqual` expects a wrong value.
The first run should end with `OK` and exit 0; the second should report `FAIL` and exit 1.
Leave `test_release.py` itself unchanged: `release.json` records its fingerprint, and changing it would make the published release out of date.

## Tags, digests, and records

A tag such as `:reviewed` is a label that can be moved later.
The digest recorded in `release.json` names the exact content that passed the tests, so later steps deploy by digest.
These local records are useful for reproducing what happened; they are not signed proof of where the image came from, which real supply chains add.

## Local shortcuts

The practice registry uses plain HTTP on a local port and inside the cluster’s Docker network, with no password.
That is acceptable for a disposable local lab, and never for a real registry.
Dockyard configures the cluster’s nodes to trust it without changing Docker Desktop’s own settings.
