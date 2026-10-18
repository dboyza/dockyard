## What you did

You scaled the API back to a number of copies that you had checked against the budget.
You added a disruption budget that lets maintenance evict one copy at a time.
You also narrowed the inventory account back to reading Pods.
The new job showed these limits still leave room for useful work.

Full access would have kept the inventory tool working, but anyone who got hold of its token could then have read Secrets or changed workloads.
"It still works" is not the same as "it is safe".

## Check your understanding

- With 3 copies, what are the total CPU requests and memory limits?
- What would a PDB with `minAvailable: 2` do to a node drain with only two copies?
- Why test permissions with the account's own identity rather than your administrator account?

## Beyond this lab

Write down the assumptions behind each limit, such as expected load and which failures you are protecting against, so the next person knows when to revisit them.
