## Pull, permit, and spread

Affinity pulled the API towards the worker pool, the toleration let it past the workers’ taint, and the spread rule put one copy on each.
Each rule did one job; none of them could do another’s.

Check your understanding:
Why would removing the workers’ taint weaken the design, even though the API would still land there?
What would happen to the second replica if one worker were full and `whenUnsatisfiable` were `DoNotSchedule`?
