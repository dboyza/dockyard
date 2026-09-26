# Repair development at the overlay

Inspect the shared base and render the development overlay.
Its replica transform is zero and its environment patch says broken.
Repair only the development overlay to request two API replicas and environment development.
Keep namespace dispatch and the base reusable.
Apply the rendered overlay, restart the API to pick up changed environment variables, and wait for rollout.
Check the actual application configuration as well as the Deployment and ConfigMap.
Render the supplied staging example for comparison, but do not apply it in this exercise.
