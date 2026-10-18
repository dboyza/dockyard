## What happened

The new API Pods had a higher priority than every batch Pod.
When they could not fit, the scheduler preempted one batch Pod and put an API Pod in its place.
The batch Deployment still asked for three replicas, so it created a replacement, which waits as Pending until a slot frees up.
Nothing was scaled down: priority decided which work waits.

Check your understanding: what would change if `batch-low` had been marked `globalDefault: true`, or if your class used `preemptionPolicy: Never`?
Why is lowering the API's request a worse answer here than giving it priority?
