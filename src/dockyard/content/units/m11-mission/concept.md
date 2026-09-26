# Mission: protect both continuity and recovery

The database has persistent storage, but its claim lifecycle and backup procedure do not meet the required durability contract.
Use the earlier storage lessons to inspect the complete ownership chain and distinguish retention from recoverability.
The prepared source data is the recovery target of this mission, not disposable filler.

A complete result preserves the source marker across Pod replacement, retains the StatefulSet's claims, restores both known records to a separate volume, and explains the remaining node-local failure boundary.
Do not treat a backup filename or a Ready Pod as sufficient evidence.
