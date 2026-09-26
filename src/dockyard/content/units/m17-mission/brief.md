# Restrict Dispatch without blocking its workflow

The environment combines excessive Secret-read access, an overly broad frontend peer, incomplete DNS permission, and a weak admission/runtime boundary.
Repair the authored sources and deploy the changes without granting broad API permissions or removing default-deny isolation.
Prove the intended and denied access paths across both nodes, test admission with a valid and invalid candidate, and inspect the actual process restrictions.
Leave a real submitted job completing through the API, queue, worker, and persistent database.
Write SECURITY-NOTES.md describing each boundary, its positive and negative evidence, and what the local exercise does not establish about production security.
