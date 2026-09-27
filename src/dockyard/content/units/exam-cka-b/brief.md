# Native cluster maintenance assessment

Recover the scheduler before starting maintenance.
The timer covers all eight outcomes in the same existing cluster.

## 1. Upgrade the existing cluster in place (25%)

Upgrade the existing kubeadm cluster from 1.34.12 to 1.35.8, including the API server, control-plane components, kubeadm, and both kubelets.
The verified target packages can be staged with `python -m dockyard.native stage-upgrade`.
Retain both original Node objects and the existing namespace and data.
Drain and maintain nodes in a safe order, return both to Ready and schedulable, and preserve package holds.
Recover the scheduler before starting this maintenance.

## 2. Renew the served API certificate (10%)

Renew the primary API serving certificate under the existing cluster CA and make the API actually serve the renewed certificate.
A changed certificate file alone is insufficient.
Do not replace the cluster CA, disable TLS verification, or rebuild the cluster.

## 3. Recover the missing static scheduler (10%)

The kube-scheduler manifest was moved out of the kubelet manifest directory to `/var/lib/dockyard/maintenance-exam/kube-scheduler.yaml` on the primary guest.
Restore the intended static component and establish a fresh scheduler assignment.
Keep the API, controller manager, etcd, and primary kubelet running.
Complete this recovery before draining or upgrading nodes.

## 4. Grant release automation a narrow scale capability (10%)

Grant ServiceAccount `release-operator` in namespace `dispatch` get and list on Deployments, and get, patch, and update on the deployments/scale subresource in that namespace.
It must not read Secrets, create Pods, or delete Deployments.
Verify effective authorization for allowed and denied operations.

## 5. Repair the stable release selector (10%)

Remove the erroneous retired-release selector from Service `dispatch` while preserving its API selector and port 8080.
The Service must have exactly the two ready API backends and serve the real application health response to the trusted frontend.
Do not enable publishNotReadyAddresses or bypass the Service.

## 6. Repair dependency egress without widening trust (15%)

Restore the API's TCP connection to the existing Redis queue on 6379.
Keep trusted frontend access, deny the untrusted frontend and outside namespace, and retain denial of unrelated API egress.
Preserve database and worker paths and both TCP and UDP DNS.
Do not disable policy enforcement or replace the network policies with an allow-all rule.

## 7. Protect one available API during voluntary disruption (10%)

Create PodDisruptionBudget `dispatch-maintenance` in namespace `dispatch` selecting both stable API replicas.
With two healthy replicas, permit exactly one voluntary disruption and preserve at least one available API replica.
Keep both replicas deployed and available for the final observation.

## 8. Prove operational continuity after maintenance (10%)

Keep the original namespace, both Node UIDs, maintenance sentinel UID and value, and seeded database row.
Demonstrate a fresh browser-ready response and a new cross-node Dispatch job that completes with the expected result in PostgreSQL.
Existing old application responses alone do not establish the final recovery contract.
