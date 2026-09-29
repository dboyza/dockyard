## Put the database back with its data

1. Follow the database’s claim to its PV and driver, and compare where the volume can be used with where `db-0` is trying to run.
2. Fix the StatefulSet’s placement so the database runs on the worker.
3. If the rollout stays stuck, delete only the failed `db-0` Pod, then wait for the database, API, and workers.
4. Choose **Check work**.

Do not delete the claim or the PV.
The original volume and data must survive, and a new job must complete.
In your notes, explain which part of the chain, from claim to mount, actually failed.
