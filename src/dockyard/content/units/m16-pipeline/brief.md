## Turn the test gate back on

The pipeline currently publishes images without running their tests, because `run_tests` is `false` in `pipeline.json`.

1. Read `pipeline.py` and `test_release.py` to see what the gate is supposed to do.
2. Set `run_tests` to `true` and run `python pipeline.py`.
3. Read the digest and source fingerprints in `release.json`.
4. Prove the gate works using the steps in Understand: a broken copy of the tests must exit non-zero. Delete the copy afterwards.
5. Choose **Check work**.

Keep the tests meaningful, and leave the published image in the lab’s registry.
