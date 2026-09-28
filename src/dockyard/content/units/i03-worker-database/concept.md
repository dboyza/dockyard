## What you’re walking into

Dispatch accepts new jobs, and they appear in the list, but none of them ever finish.
The API’s `/readyz` check is green, and the database and queue are running normally.
Just before the problem started, someone changed settings that apply only to the workers.

Your job is to find out why the workers are not finishing jobs and fix it, without losing any stored jobs.

## How to approach an incident

1. **Describe the symptom** in one sentence, in terms a user would notice.
2. **Collect evidence** before changing anything.
3. **Form a theory** that explains all of that evidence.
4. **Make the smallest fix** that addresses the cause.
5. **Check the result** the way a user would, with a new job.

Write each step in your notes as you go.
Hints and the reference solution are available, but using them marks this attempt as practice with help.

## Useful reminders

The API and workers are built from the same image, but each service in `compose.yaml` can have its own settings.
A healthy API only tells you the API’s own connections work.
`docker compose logs worker` shows what the workers are doing, or failing to do.
