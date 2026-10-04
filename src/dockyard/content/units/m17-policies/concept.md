## Rules the API server enforces

RBAC decides *who* may change an object.
It cannot say anything about *what* the object contains: an allowed user can still create a Deployment with no memory limit, which lets one runaway process take memory from everything else on its node.
Rules about content belong to **admission control**.

Every request that creates or changes an object passes through several stages in the API server.
It is authenticated, then authorized, then handed to admission controllers, and only then stored.
An admission controller can change the object, called mutating, or check it and refuse it, called validating.
You have already used one validating admission controller: Pod Security Admission, which enforces the Restricted standard.

```figure
admission-policy
```

## ValidatingAdmissionPolicy

A **ValidatingAdmissionPolicy** lets you write your own validating rule, without running any extra software.
The rule is an expression in **CEL**, the Common Expression Language, evaluated against the object in the request:

```yaml
apiVersion: admissionregistration.k8s.io/v1
kind: ValidatingAdmissionPolicy
metadata:
  name: require-memory-limits
spec:
  failurePolicy: Fail
  matchConstraints:
    resourceRules:
    - apiGroups: ["apps"]
      apiVersions: ["v1"]
      operations: ["CREATE", "UPDATE"]
      resources: ["deployments"]
  validations:
  - expression: >-
      object.spec.template.spec.containers.all(c,
        has(c.resources) && has(c.resources.limits) && 'memory' in c.resources.limits)
    message: Every container needs a memory limit.
```

`matchConstraints` says which requests the policy looks at, here creating or updating Deployments.
The expression reads like a sentence: for all containers `c`, `c` has resources, has limits, and its limits include `memory`.
When it is false, the request fails the check and the message explains why.

A policy on its own does nothing.
A **ValidatingAdmissionPolicyBinding** puts it into effect and says where and how:

```yaml
apiVersion: admissionregistration.k8s.io/v1
kind: ValidatingAdmissionPolicyBinding
metadata:
  name: require-memory-limits
spec:
  policyName: require-memory-limits
  validationActions: [Deny]
  matchResources:
    namespaceSelector:
      matchLabels:
        kubernetes.io/metadata.name: dispatch
```

`validationActions` decides what a failed check does: `Deny` refuses the request, `Warn` lets it through with a warning, and `Audit` only records it in the audit log.
`matchResources` narrows where the binding applies; without it, the binding applies to the whole cluster.
Every namespace carries the label `kubernetes.io/metadata.name` with its own name, which makes selecting one namespace easy.

## Test without creating anything

A **server-side dry run** sends the request through every stage, admission included, then stops before storing it:

```sh
kubectl create deployment probe --image=busybox --dry-run=server -n dispatch
```

That Deployment has no memory limit, so it is a quick way to test the rule.
A refusal looks like `ValidatingAdmissionPolicy 'require-memory-limits' with binding 'require-memory-limits' denied request: Every container needs a memory limit.`
A warning starts with `Warning:` and the command still succeeds.

## The situation in this lab

The platform team wrote the policy in `policy.yaml`, but limitless Deployments are still being created in `dispatch`.
The policy is correct; the binding is not.
It only warns, and it has no namespace selection, so it would also apply to the `sandbox` namespace, where experiments are allowed to skip limits.

## Fix it

1. Try the dry run above in `dispatch` and in `sandbox`, and read what each returns.
2. In `policy.yaml`, change the binding to `validationActions: [Deny]`.
3. Add `matchResources.namespaceSelector` so the binding applies only to `dispatch`.
4. Run `sh run.sh`, then repeat both dry runs.

The dry run in `dispatch` should now be refused with the policy's message, and the one in `sandbox` should succeed.
Dispatch's own Deployments all declare memory limits, so they keep rolling out normally.

## If something goes wrong

- **Dispatch's Deployments are refused after your change**: the expression is checking more than memory limits, or a container lost its limit. Read the refusal message in `sh run.sh`'s output.
- **The `sandbox` dry run is refused too**: the binding has no `matchResources`, or the selector does not name `dispatch`.
- **Nothing is refused at all**: check `kubectl get validatingadmissionpolicybindings` and confirm the binding's `policyName` matches the policy's name.
