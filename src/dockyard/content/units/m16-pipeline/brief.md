# Restore the publication gate

The prepared pipeline publishes a candidate while run_tests is false.
Inspect pipeline.py and its supplied HTTP tests, then enable the gate in pipeline.json.
Run python pipeline.py and inspect the resulting digest and source hashes in release.json.
Keep the tests meaningful and leave the published image available in the owned registry.
Verify that introducing a failing assertion in a temporary test copy produces a nonzero test process before trusting the gate; restore the original tests afterward.
