# Repair, replace, restore, and explain

Correct both StatefulSet claim-retention policies in `platform.yaml` and the incomplete dump in `backup.sh`.
Preserve the source's existing claim and data.
Apply the manifest, run `python storage-proof.py`, and run the repaired backup script.

Verify the original marker from a replacement source Pod and query the two recovery records from db-restore-0.
Compare source and target claim UIDs and PV names to establish independent storage.
Keep the source application available after the deliberate replacement interruption.

Write a runbook with the exact source, destination, expected records, verification commands, and the circumstances this local setup does not survive.
Use an independent retake to repeat the diagnosis without revealed reference files.
