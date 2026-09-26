Drain the extra worker `lima-$DOCKYARD_NODE_PREFIX-worker2` and leave it cordoned.
Retain a disruption budget selecting the two stable Dispatch API replicas and protecting at least one available replica during eviction.
Do not delete the Node or bypass the eviction API.
Two API replicas must become available on remaining capacity, the original stored sentinel must survive, and a fresh job must complete.
Inspect workload ownership and the node-local database placement before running maintenance.
