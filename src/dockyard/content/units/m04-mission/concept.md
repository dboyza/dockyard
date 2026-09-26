## A replacement would currently destroy the data

The supplied API has an important original job, but the database lives in its container writable layer.
The next deployment must replace that container.
Your task is to preserve the record, move it into a named volume, and leave a working service that uses the durable storage path.

This mission combines lifecycle, identity, permissions, and restore verification.
Start by locating the original database and deciding how to obtain a consistent copy.
Do not remove the current container until the backup is available.
The original source is a disposable practice resource, but treating it carefully is the point of the exercise.
