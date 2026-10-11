#!/bin/sh
set -eu
registry=$(cat registry.txt)
# The release's digest, as the registry reports it.
digest=$(curl -sfI -H 'Accept: application/vnd.oci.image.manifest.v1+json' \
  -H 'Accept: application/vnd.docker.distribution.manifest.v2+json' \
  "http://$registry/v2/dispatch/manifests/1.0" | tr -d '\r' | awk 'tolower($1)=="docker-content-digest:" {print $2}')
release="$registry/dispatch@$digest"
# A key pair for signing; the private key is protected by a password.
export COSIGN_PASSWORD=practice-signing-password
[ -f cosign.key ] || cosign generate-key-pair
cosign sign --key cosign.key --use-signing-config=false --tlog-upload=false --yes "$release"
cosign verify --key cosign.pub --insecure-ignore-tlog=true "$release" > /dev/null
# Admit only release images, then deploy production by the verified digest.
sed "s#REGISTRY/#$registry/#" release-policy.yaml | kubectl apply -f -
sed "s#\${DOCKYARD_IMAGE}#$release#" production.yaml > production.yaml.new && mv production.yaml.new production.yaml
sh run-apply.sh
kubectl rollout status deployment/dispatch -n production --timeout=120s
