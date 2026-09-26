# Connect the HPA to the real workload

The HPA points at dispatch-missing instead of the existing Deployment.
Repair `autoscale.yaml`, preserve CPU requests, and apply it.
The supplied load Deployment is already sending requests to `/work`.
Use `python wait-scale.py` or equivalent bounded observation to wait for four available API replicas.
Inspect current CPU metrics and the HPA conditions that explain the decision.

Keep minReplicas 2, maxReplicas 4, and a 50 percent CPU target.
Keep the disruption budget selecting the stable API with minAvailable 2.
Do not replace measured scaling with a manual replicas=4 edit or remove the HPA after scaling.
Pause the owned lab when finished to stop the deliberate CPU load.
