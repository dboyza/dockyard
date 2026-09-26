# Recover the release and its source values

Inspect `helm history dispatch -n staging` and the live Deployment.
Revision 1 was healthy; the starter's second revision deliberately scaled the API to zero.
Rollback to revision 1 using Helm and wait for the API to become available.
Fix `values-practice.yaml` to api.replicas 2 and environment staging.
Keep the chart, release name, namespace, and private credential delivery intact.
Verify Helm's deployed revision values, the rollback history, the available Pods, and the application's environment response.
A manual kubectl scale alone leaves the release's intended values incorrect and does not complete the repair.
