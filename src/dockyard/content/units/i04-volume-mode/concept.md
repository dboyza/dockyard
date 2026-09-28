## What you’re walking into

After some maintenance on file permissions, Dispatch can still answer health checks and show its existing job.
But every attempt to save a new job fails.

Your job is to find the cause and restore saving, while keeping the original job and running the API as its ordinary user, number 10001.

## How to approach an incident

1. **Describe the symptom** in one sentence, in terms a user would notice.
2. **Collect evidence** before changing anything.
3. **Form a theory** that explains all of that evidence.
4. **Make the smallest fix** that addresses the cause.
5. **Check the result** the way a user would, by saving a new job.

Write each step in your notes as you go.
Hints and the reference solution are available, but using them marks this attempt as practice with help.

## Reading file permissions

`ls -ln` lists files with their permissions and numeric owners.
The first column, such as `-rw-r-----`, shows three groups of three letters after the first character: what the owner, the group, and everyone else may do.
`r` means read, `w` means write, and `-` means that permission is missing.
`chmod u+w file` gives the owner write permission; `chmod o+w file` would give everyone write permission, which is far more than an app needs.

The Linux primer in the reference desk explains permissions in more detail.
