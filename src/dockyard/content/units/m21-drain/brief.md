## Drain the extra worker safely

1. Look at the Pods on `lima-$DOCKYARD_NODE_PREFIX-worker2`, who owns them, where the database lives, and the disruption budget.
2. Change the budget so at least one of the two stable API copies must stay available, which allows one eviction.
3. Drain `lima-$DOCKYARD_NODE_PREFIX-worker2` with the command from Understand, and leave it cordoned.
   Wait for `kubectl rollout status deployment/dispatch` so the replacement copy is running before you check.
4. Choose **Check work**.

Do not delete the Node or bypass evictions.
Two API copies must end up available on the remaining nodes, the stored data must survive, and a new job must complete.
