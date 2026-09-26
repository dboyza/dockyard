#!/bin/sh
set -eu
kubectl create configmap coredns -n kube-system --from-file=Corefile=Corefile.original --dry-run=client -o yaml | kubectl apply -f -
kubectl rollout restart deployment/coredns -n kube-system
kubectl rollout status deployment/coredns -n kube-system --timeout=120s
kubectl set image daemonset/kube-proxy -n kube-system kube-proxy=registry.k8s.io/kube-proxy:v1.35.8
kubectl rollout status daemonset/kube-proxy -n kube-system --timeout=180s
