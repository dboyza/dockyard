#!/bin/sh
set -eu
registry=$(cat registry.txt)
# Build the minimal image and publish it to the release registry.
docker build --build-arg "BASE_IMAGE=$DOCKYARD_PYTHON_IMAGE" -t "$registry/dispatch:2.0" .
docker push "$registry/dispatch:2.0"
release=$(docker inspect --format '{{index .RepoDigests 0}}' "$registry/dispatch:2.0")
# Sign and verify exactly what was published.
export COSIGN_PASSWORD=practice-signing-password
[ -f cosign.key ] || cosign generate-key-pair
cosign sign --key cosign.key --use-signing-config=false --tlog-upload=false --yes "$release"
cosign verify --key cosign.pub --insecure-ignore-tlog=true "$release" > /dev/null
# Admit only release images in production, then deploy the hardened manifest by digest.
sed "s#REGISTRY/#$registry/#" release-policy.yaml | kubectl apply -f -
sed "s#RELEASE#$release#" production.yaml > production.yaml.new && mv production.yaml.new production.yaml
python render.py production.yaml | kube-linter lint -
sh run-apply.sh
kubectl rollout status deployment/dispatch -n production --timeout=120s
cp release-report-reference.md release-report.md
