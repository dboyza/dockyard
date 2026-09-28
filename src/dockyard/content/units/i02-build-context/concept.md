## What you’re walking into

The team edited `VERSION` in the workspace to `incident-release-v2` and ran the release script, `release.sh`.
The build succeeded.
But a brand-new container from that image still reports `incident-release-v1`.

Something between the edit and the running container is using old files.
Your job is to find where, fix it properly, and ship the new release.

## How to approach an incident

1. **Describe the symptom** in one sentence, in terms a user would notice.
2. **Collect evidence** before changing anything.
3. **Form a theory** that explains all of that evidence.
4. **Make the smallest fix** that addresses the cause.
5. **Check the result** the way a user would, with a fresh request.

Write each step in your notes as you go.
Hints and the reference solution are available, but using them marks this attempt as practice with help.

## Useful reminders

The last argument of `docker build` is the **build context**, the folder whose files Docker may copy.
`COPY VERSION ./` copies `VERSION` from that folder, whichever folder it is.
Read `release.sh` and list the workspace with `ls -R` before you rebuild anything.
