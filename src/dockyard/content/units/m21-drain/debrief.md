# Debrief: Drain a worker without bypassing availability protection

The extra worker is evacuated while the remaining replicas and disruption budget continue to protect the intended availability.
Drain operates through eviction semantics; bypassing those protections would avoid the operational decision the exercise asks you to make.

## Explain your result

Which observation proved the target was evacuated, and which proved the application still had useful capacity elsewhere?

## Transfer beyond this lab

Before a production drain, identify non-evictable workloads, local data, spare capacity, and the conditions under which the maintenance must stop.
