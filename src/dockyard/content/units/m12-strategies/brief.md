# Bring the candidate into a controlled preview

The prepared candidate image contains release dispatch-release-2, but its Deployment has zero replicas and the preview Service mistakenly selects the stable track.
Repair `canary.yaml` and `preview.yaml` to run one candidate and route preview requests only to it.
Preserve two stable replicas and the primary Service selector app=dispatch so all three ready endpoints participate there.
Apply the files and inspect both EndpointSlices and actual release responses.

Do not change the stable Deployment's selector or image to impersonate a candidate.
The reference builds the supplied candidate with `sh candidate.sh` when needed.
Explain how you would promote or abort this release and why a replica ratio alone is not precise HTTP traffic weighting.
