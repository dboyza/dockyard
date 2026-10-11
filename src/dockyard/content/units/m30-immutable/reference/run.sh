#!/bin/sh
set -eu
# Replicas started from one image should hold identical files. Fingerprint each one's
# program and configuration folders; the odd one out has been changed.
for pod in $(kubectl get pods -n uploads -l app=uploader -o name); do
  print=$(kubectl exec -n uploads "$pod" -- sh -c 'find /usr /etc /bin /sbin -xdev -type f ! -path /etc/hosts ! -path /etc/hostname ! -path /etc/resolv.conf -exec md5sum {} + 2>/dev/null | sort | md5sum')
  echo "$print ${pod#pod/}"
done | sort > fingerprints.txt
cat fingerprints.txt
# The fingerprint that appears only once belongs to the tampered Pod.
awk '{print $1}' fingerprints.txt | uniq -u | while read -r odd; do
  grep "^$odd" fingerprints.txt | awk '{print $NF}' > tampered-pod.txt
done
cat tampered-pod.txt
# Make the containers immutable; the rollout replaces every Pod, including the tampered one.
python render.py uploads.yaml | kubectl apply -f -
kubectl rollout status deployment/uploader -n uploads --timeout=120s
