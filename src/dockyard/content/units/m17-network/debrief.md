## Allowed on purpose, blocked on purpose

The corrected peer now requires the right namespace *and* the right label, and DNS works over both protocols.
Check work proved it both ways: allowed paths connected, and blocked paths failed while their targets were demonstrably up.

Check your understanding:
Which blocked request proves the boundary is enforced, and which allowed request proves you did not just break everything?
Rewrite the `from` list so that *either* the frontend namespace *or* any Pod labelled `app: trusted` in `dispatch` is allowed.
