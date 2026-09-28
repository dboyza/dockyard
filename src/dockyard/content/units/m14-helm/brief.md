## Roll back the release and fix its values

1. Look at `helm history dispatch -n staging` and the live Deployment in `staging`.
2. Roll back to revision 1 with Helm and wait for the API to become available.
3. Fix `values-practice.yaml` to `api.replicas: 2` and `environment: staging`.
4. Check Helm’s current values, the rollback in the history, the running Pods, and Dispatch’s environment.
5. Choose **Check work**.

Keep the chart, release name, namespace, and private password file as they are.
A plain `kubectl scale` would leave the release’s recorded values wrong, so it does not count as a fix.
