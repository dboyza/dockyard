## What you’re walking into

Someone tidied up the namespace’s egress NetworkPolicies.
Since then, requests to Dispatch fail and the workers keep logging dependency errors.
Oddly, the trusted frontend can still connect to the API’s address.

## How to approach an incident

1. **Describe the symptom** in one sentence, in terms a user would notice.
2. **Collect evidence** before changing anything.
3. **Form a theory** that explains all of that evidence.
4. **Make the smallest fix** that addresses the cause.
5. **Check the result** with a new job from the trusted frontend.

Write each step in your notes as you go.
Hints and the reference solution are available, but using them marks this attempt as practice with help.

## Useful reminders

- Reaching an address by number and looking up a name are separate things. DNS needs its own egress rule, on port 53, over both UDP and TCP.
- Ports in a policy must match exactly: allowing 5433 does nothing for a database on 5432.
- A connection can be blocked by the sender’s egress rules *or* the receiver’s ingress rules.
- One successful connection does not show every path works; test each dependency separately.

The boundary you must keep:

- the trusted frontend reaches the API, but not PostgreSQL directly;
- the untrusted frontend, and a trusted-looking client in another namespace, cannot reach the API;
- the API and workers reach PostgreSQL and Redis;
- the API cannot reach the unrelated outside target.

Removing the policies would make everything connect and break that boundary, so it does not count as a fix.
