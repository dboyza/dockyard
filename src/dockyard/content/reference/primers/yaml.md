# Read YAML as a data structure

YAML represents mappings, lists, and scalar values.
Kubernetes reads those values as API objects; indentation is part of the structure.
Use spaces for indentation, and inspect the parent field of each value before editing it.

## A small example outside the lab

```yaml
service:
  name: report-worker
  replicas: 2
  labels:
    team: platform
  ports:
    - name: http
      port: 8080
  enabled: true
  release: "1.0"
```

`service` contains a mapping.
`ports` contains a list with one mapping as its item.
`replicas` is an integer, `enabled` is a boolean, and the quoted release is a string.
Indenting `labels` under a different parent would change its meaning even if the YAML remained syntactically valid.
Quote values when they must remain strings, especially values that resemble numbers or booleans.

## Syntax validity is only the first boundary

A parser can accept YAML that does not satisfy the receiving API's schema.
A Kubernetes schema can accept an object whose selectors match no Pods.
The API can accept a Deployment whose image never starts successfully.
These are separate questions: can the data be parsed, is its structure valid for this API, and does the resulting system work?
Use live observations after applying a manifest.

## Common Kubernetes structure

`apiVersion` and `kind` identify the API and resource type.
`metadata` names and labels the object.
For a Deployment, `spec.template` describes the Pods it will create.
Labels on the Deployment itself and labels on its Pod template live at different paths.
A Service selects Pod labels; it does not select the Deployment's name automatically.

```yaml
metadata:
  name: example
  labels:
    owner: practice
spec:
  template:
    metadata:
      labels:
        app: example
```

Here `owner: practice` labels the outer object, while `app: example` labels future Pods.
A Service looking for `app: example` therefore needs the second location.

## Multiple documents and multiline values

A line containing `---` separates YAML documents.
Applying a file can submit several objects, and a failure partway through is not a transaction that automatically rolls back earlier successes.
A block introduced by `|` preserves line breaks; `>` generally folds text lines.
These scalar styles matter when storing configuration files in a ConfigMap.
Comments begin with `#` outside quoted text and are not sent as object data.

## Template text is not automatically expanded

`${DOCKYARD_IMAGE}` in a YAML file is literal text unless a rendering step replaces it.
Dockyard checkpoints explicitly use `python render.py FILE` where replacement is intended.
Plain `kubectl apply -f FILE` does not perform shell-variable substitution inside that file.
Inspect the rendered result when a value seems surprising.

## Check your understanding

Locate a Deployment's own labels, its Pod template labels, and a Service selector in one checkpoint.
Explain why valid YAML can still produce a Service with no usable endpoints.
