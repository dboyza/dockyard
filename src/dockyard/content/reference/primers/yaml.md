# Reading YAML

**YAML** is a text format for writing structured settings.
Docker Compose files and Kubernetes files are both written in YAML, so learning to read it pays off quickly.

## The three building blocks

```yaml
service:
  name: report-worker
  replicas: 2
  enabled: true
  release: "1.0"
  labels:
    team: platform
  ports:
    - name: http
      port: 8080
```

1. A **mapping** is a set of `key: value` pairs. `service:` is a key whose value is everything indented beneath it.
2. A **list** is a series of items, each starting with `- `. `ports` holds a list with one item.
3. A **scalar** is a single value: text, a number, or `true`/`false`.

**Indentation is meaning.**
Everything indented under a key belongs to it.
Use spaces, never tabs, and keep items at the same level lined up exactly.
Moving `labels:` two spaces to the left would make it a sibling of `service` instead of part of it, and YAML would not warn you.

```figure
yaml-building-blocks
```

YAML guesses the type of unquoted values.
`2` is a number, `true` is a yes/no value, and `1.0` would become a number too, which is why the example quotes `"1.0"` to keep it as text.
When in doubt, quote values that must stay as text.

A key must appear only once in each mapping.
If you accidentally write the same key twice, such as two `livenessProbe:` entries in one container, most tools keep only the last one without any warning.

Lists can also be written on one line in square brackets: `[python, worker.py]` means the same as a two-item list.

## Valid is not the same as working

There are three separate questions:

1. **Is it valid YAML?** Can it be read at all?
2. **Is it a valid object?** Does it have the fields the tool expects, with the right types?
3. **Does it work?** Does the running system behave as you intended?

A file can pass the first two and still fail the third.
For example, Kubernetes will happily accept a Service that points at labels no Pod has.
Always check the running result, not just that the file was accepted.

```figure
yaml-three-checks
```

## How Kubernetes files are laid out

Every Kubernetes object has the same outline:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: example
  labels:
    owner: practice
spec:
  replicas: 2
  template:
    metadata:
      labels:
        app: example
```

- `apiVersion` and `kind` say what type of object this is.
- `metadata` holds its name and **labels**, short tags used to find and group objects.
- `spec` describes what you want the object to be.

Notice there are two sets of labels.
`owner: practice` labels the Deployment itself.
`app: example`, inside `spec.template`, labels the Pods the Deployment will create.
A Service that should find those Pods must look for `app: example`.

```figure
yaml-two-label-sets
```

`kubectl explain deployment.spec.template` describes any field from the command line, which is handy when you forget where something goes.

## More than one object in a file

A line containing only `---` separates one YAML document from the next, so one file can hold several objects.
If applying a file fails partway through, the objects already created stay created; nothing is rolled back automatically.

A value starting with `|` keeps its line breaks exactly, which is useful for embedding a small file:

```yaml
config.ini: |
  mode=practice
  retries=3
```

`#` starts a comment, which is ignored.

## Placeholders are not filled in automatically

Text such as `${DOCKYARD_IMAGE}` inside a YAML file stays as those exact characters unless something replaces it.
Docker Compose fills these in, but `kubectl apply -f file` does not.
Where a Dockyard lab needs this, it supplies a helper such as `python render.py FILE`; look at its output if a value surprises you.

## Check your understanding

In one of the lab’s Kubernetes files, find the Deployment’s own labels, its Pod template labels, and the Service’s selector.
Why could a perfectly valid file still produce a Service that sends traffic nowhere?
