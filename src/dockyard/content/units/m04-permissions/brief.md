## Restore the write path

Prepare starts the non-root API with a labeled volume whose directory has the wrong owner.
Observe that `/healthz` works while POST /jobs fails.
Compare the API identity with `/data` ownership, then repair the assigned volume's access.

Keep the API non-root and do not grant world-write access.
Keep the same named volume, and prove new jobs can be written and independently read.
No application source change is needed.
