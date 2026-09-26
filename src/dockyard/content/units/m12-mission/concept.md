# Capstone: release evidence across the application stack

Dispatch now has a database with persistent storage, externalized configuration, workers, and an API with explicit health contracts.
A release is safe only when those contracts continue to hold together.
This capstone combines a bad image, an unsafe availability budget, mismatched probes, and an unavailable candidate preview.
Use the earlier modules to form and test one hypothesis at a time.

The required result is a healthy stable release beside a separately identifiable candidate, with startup protected, readiness meaningful, and process termination observed.
A successful check exports a checkpoint with the source and assessment evidence.
Your written release runbook should make the operational decision reproducible for another engineer.
