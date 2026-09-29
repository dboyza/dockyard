# Operating handoff

## Symptom and evidence

- Dispatch requests failed. `kubectl get endpointslices -l kubernetes.io/service-name=dispatch` listed no endpoints, and the Service selected `track: retired` while the API Pods are labelled `track: stable`.
- After fixing the route, new jobs stayed `queued`. `kubectl get deployment worker` showed 0 replicas.

## Repair and verification

- `kubectl patch service dispatch` to select `track: stable`; the EndpointSlice then listed both API Pods.
- `kubectl scale deployment/worker --replicas=1`, then `kubectl rollout status deployment/worker`.
- A new job reached `done`, and the job stored before the incident is still in the database.

## Recovery boundaries and next actions

Nothing in the database or queue was changed.
Find out who changed the selector and the worker count, and why, before closing the incident.
