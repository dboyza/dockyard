## One image, two environments

Teams often run the same image in several environments, each with its own settings and passwords.
In this mission you will run Dispatch twice from one image: the normal `dispatch` environment and a `preview` environment, each in its own namespace.

Namespaces let both environments use the same object names.
Each has a Service called `dispatch` and a Secret called `dispatch-database`.
Inside a namespace, `dispatch` means that namespace’s Service.
From anywhere, `dispatch.preview.svc.cluster.local` means the preview one specifically.

Be careful about what namespaces do *not* do.
They separate names and permissions, but Pods in different namespaces can still talk to each other freely.
Blocking traffic needs NetworkPolicies, which come later.

There are no step-by-step commands.
Use `-n preview` or `-n dispatch` on every command so you always know which environment you are looking at.

## Working on your own

Try it without hints first.
Hints and the reference solution are available, but using them marks this attempt as practice with help.
