## What changed

The policy always described the rule correctly, but a policy is only a description.
The binding put it into effect: `Deny` made a failed check refuse the request, and the namespace selector kept the rule to `dispatch`.
Admission runs inside the API server, so the rule applies to every client: `kubectl`, controllers, and pipelines alike.
A server-side dry run shows the outcome without changing anything.

Check your understanding: if an existing Deployment in `dispatch` had no memory limit when you bound the policy, would it stop running?
What would happen the next time someone updated it?
