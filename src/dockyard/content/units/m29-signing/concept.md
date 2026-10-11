## Knowing what you run

An image name such as `dispatch:1.0` says nothing about who built it.
Tags can be moved to different content, registries can be compromised, and a laptop build can end up in production.
Two practices close those gaps:

- **Signing**: whoever produces a release signs its **digest**, the checksum that identifies exactly that content. Anyone with the matching public key can later prove the image is unchanged and came from the key holder.
- **Admission rules**: the cluster only accepts images from approved registries, referenced by digest, so nothing else can be deployed by accident or on purpose.

```figure
image-signing
```

## Signing with cosign

**cosign**, from the Sigstore project, signs and verifies container images.
It stores each signature in the same registry, beside the image it signs.
This lab uses a key pair you create, which works entirely offline:

```sh
export COSIGN_PASSWORD=choose-a-password
cosign generate-key-pair
```

That writes `cosign.key`, the private key, encrypted with the password, and `cosign.pub`, the public key you can share.
Keep the private key secret; in a real team it would live in a key management service.

The release is already in this lab's registry, whose address is in `registry.txt`, as `dispatch:1.0`.
Find the digest the tag points to right now:

```sh
curl -sI -H 'Accept: application/vnd.oci.image.manifest.v1+json' -H 'Accept: application/vnd.docker.distribution.manifest.v2+json' "http://$(cat registry.txt)/v2/dispatch/manifests/1.0" | grep -i docker-content-digest
```

Then sign and verify by digest:

```sh
cosign sign --key cosign.key --use-signing-config=false --tlog-upload=false --yes "$(cat registry.txt)/dispatch@sha256:DIGEST"
cosign verify --key cosign.pub --insecure-ignore-tlog=true "$(cat registry.txt)/dispatch@sha256:DIGEST"
```

Replace `DIGEST` with the value you found.
Normally cosign also records each signature in a public **transparency log**, Rekor, so anyone can audit what was signed and when.
That needs the internet, so these flags skip it; on a real project you would keep it.

## Deploy by digest

A Deployment that names `dispatch:1.0` gets whatever the tag points to when a node pulls it.
A Deployment that names `registry/dispatch@sha256:...` gets exactly the content you verified, every time.

## Admitting only release images

A ValidatingAdmissionPolicy, which you met in module 17, can check every image in a request:

```yaml
variables:
- name: containers
  expression: "object.kind == 'Pod' ? object.spec.containers : object.spec.template.spec.containers"
validations:
- expression: "variables.containers.all(c, c.image.startsWith('REGISTRY/') && c.image.contains('@sha256:'))"
  message: Production images must come from the release registry, pinned by digest.
```

Replace `REGISTRY` with the address in `registry.txt`, match Deployments and Pods, and bind it with `Deny` to the `production` namespace only.

```figure
release-admission
```

This policy enforces where images come from and that they are pinned, but it cannot check signatures itself.
Production clusters add an admission controller that verifies signatures, such as Sigstore's policy-controller or Kyverno, which needs access to keys and, usually, the transparency log.
Here, verification happens in your release step, before you deploy.

## Fix it

1. Generate a key pair, then sign and verify the release by its digest.
2. Write `release-policy.yaml` with the policy and binding for `production`, and apply it.
3. Change the image in `production.yaml` to the release by digest, and apply with `sh run.sh`.
4. Test the policy with `kubectl create deployment test -n production --image=busybox --dry-run=server`, which should be refused.

## If something goes wrong

- **`cosign sign` asks for a password and fails**: export `COSIGN_PASSWORD` with the password you used for the key pair.
- **The Deployment is refused after the policy is in place**: its image is a tag or comes from elsewhere. Use `REGISTRY/dispatch@sha256:...` exactly.
- **The Pod is stuck in `ErrImagePull`**: check the digest is complete and the registry address matches `registry.txt`.
