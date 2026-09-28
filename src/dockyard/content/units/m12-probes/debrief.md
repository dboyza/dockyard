## The right signal for each decision

The startup probe gave Dispatch time to warm up, liveness only restarts a genuinely stuck process, and readiness keeps traffic away while dependencies are unavailable.

Check your understanding:
Why does putting a database check in the liveness probe make a database outage worse?
Your app takes up to 50 seconds to start. Write a startup probe with a period of 5 seconds that allows for that.
