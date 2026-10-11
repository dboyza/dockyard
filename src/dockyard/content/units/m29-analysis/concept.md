## Finding problems before they are deployed

Most security mistakes in Kubernetes are written down long before they run: a `privileged: true` copied from a forum answer, a `hostPath` mount added "just in case", a container with no resource limits.
**Static analysis** reads manifests without running them and reports risky settings, so a reviewer, or a pipeline, can catch them before they reach a cluster.

This lesson uses two widely used analysers, both installed in your lab terminal:

- **KubeLinter** checks manifests against a list of rules and reports each problem with a remediation. It exits with an error when it finds any, which makes it easy to use as a pipeline gate.
- **kubesec** gives each workload a **risk score**: points for good settings, a large penalty for critical ones such as privileged containers, and advice on what would raise the score.

```figure
static-analysis
```

## Analyse what you deploy

Your workspace manifests contain placeholders such as `${DOCKYARD_IMAGE}`, which `render.py` fills in when you deploy.
Analyse the rendered result, because that is what the cluster receives; both tools read a manifest from standard input when given `-`:

```sh
python render.py resizer.yaml | kube-linter lint -
python render.py resizer.yaml | kubesec scan -
```

Run against the raw file, KubeLinter would complain that `${DOCKYARD_IMAGE}` is not a valid image name, a finding about the template rather than the workload.

## Reading the findings

KubeLinter prints one finding per problem, naming the object, the container, the check, and a remediation, for example `container "resizer" is privileged (check: privileged-container ...)`.

kubesec prints a JSON report per object.
For the Deployment, `score` is the total, `scoring.critical` lists what caused large penalties, and `scoring.advise` lists improvements with their points.

```figure
risk-score
```

The resizer's findings fall into a few groups:

- **Privilege**: `privileged: true` gives the container nearly all of the node's power. It does not need it.
- **Host access**: a `hostPath` volume mounts the node's whole filesystem into the container. Remove it.
- **Identity**: run as a non-root user with `runAsNonRoot: true` and `runAsUser: 10001`, which this image supports, and drop all Linux capabilities.
- **Immutability**: `readOnlyRootFilesystem: true`, with the existing `emptyDir` at `/work` for the thumbnails.
- **Resources**: requests and limits for CPU and memory, so one container cannot starve the node.
- **API access**: a dedicated ServiceAccount with `automountServiceAccountToken: false`, because the resizer never calls the API.

## Tools are input, not truth

Analysers lag behind Kubernetes and encode one set of opinions.
For example, this version of kubesec still advises `SeccompAny` even when the Pod sets `seccompProfile: RuntimeDefault`, because it looks for an older annotation.
Read each finding, fix the real problems, and know which remaining advice you are choosing to ignore and why.

## Fix it

1. Run both tools on the rendered `resizer.yaml` and read every finding.
2. Rewrite `resizer.yaml` until KubeLinter reports no errors and kubesec scores the Deployment at least 10 with no critical findings.
3. Deploy it with `sh run.sh`, and confirm the resizer keeps making thumbnails: `kubectl logs -n media deploy/resizer`.

## If something goes wrong

- **KubeLinter reports `non-existent-service-account`**: a `serviceAccountName` refers to an account that is not in the same file. Add the ServiceAccount to `resizer.yaml`.
- **The new Pod fails with a permission error**: something writes outside `/work`. Read the log for the path; the resizer itself needs only `/work`.
- **kubesec still scores below 10**: read the `advise` list for the Deployment; each entry names a setting and the points it is worth.
