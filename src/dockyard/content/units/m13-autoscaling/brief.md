## Point the autoscaler at Dispatch

The HPA targets a Deployment called `dispatch-missing`, which does not exist.

1. Look at `kubectl describe hpa dispatch` and its conditions.
2. Fix `autoscale.yaml` so it scales the `dispatch` Deployment, and apply it. Keep 2 to 4 replicas, a 50% CPU target, and the API’s CPU requests.
3. The supplied load generator is already sending work. Run `python wait-scale.py` to wait for four available API replicas.
4. Look at `kubectl top pods` and the HPA’s conditions, and explain its decision.
5. Choose **Check work**.

Keep the disruption budget at `minAvailable: 2` for the stable API.
Do not set four replicas by hand or delete the HPA afterwards.
Stop the lab when you have finished, to stop the load generator.
