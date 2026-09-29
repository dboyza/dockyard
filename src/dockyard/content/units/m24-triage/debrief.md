## Compare your triage

There were two separate faults.
The Service selected `track: retired`, a label no running Pod had, so requests went nowhere even though the API Pods were healthy.
With the route fixed, jobs were accepted but stayed `queued`, because the worker Deployment had been scaled to zero.
Neither fix alone was enough, and the second fault only showed once the first was fixed.

## Check your understanding

- Which observation told you the API Pods were healthy but unreachable?
- What else could make jobs stay `queued`, and how would you tell those causes apart?
- Why is re-running a setup script a risky way to fix a shared system?

## Beyond this lab

In a real incident, also say out loud who is affected, how urgent it is, and whether you are allowed to make the change.
Keep your notes as you go; they are the start of the handoff.
