#!/bin/sh
set -eu
# Who holds what, and how much can each subject really do?
kubectl get clusterrolebindings -o wide | grep -vE '^(system:|kubeadm:|calico)' || true
kubectl auth can-i --list --as=system:serviceaccount:ci:deployer | head -5
kubectl auth can-i --list --as=alex --as-group=dispatch-operators | head -5
# Replace the broad grants with namespaced, least-privilege ones.
kubectl delete clusterrolebinding ci-deployer-admin dispatch-operators-all
kubectl delete clusterrole dispatch-ops
kubectl apply -f rbac.yaml
kubectl auth can-i patch deployments -n dispatch --as=system:serviceaccount:ci:deployer
kubectl auth can-i get secrets -n dispatch --as=alex --as-group=dispatch-operators || true
