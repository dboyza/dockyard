## Remove an unused vulnerable library

1. Run `python scan.py before` and find CVE-2022-29217 and PyJWT in `scan-before.json` and `sbom-before.json`.
2. Set `include_legacy_dependency` to `false` in `build.json`.
3. Run `sh repair-image.sh`, which rebuilds the image, restarts the API and worker, and writes the `after` reports.
4. Confirm the CVE and PyJWT are gone from the after reports, and note what findings remain.
5. Choose **Check work**.

Check work scans the current image itself and checks the running Python processes do not have the library.
