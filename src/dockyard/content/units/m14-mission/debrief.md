## Clear ownership, reproducible environments

Each environment came back from its own source: an overlay, a Helm release, and a custom resource.
Because no object had two owners, none of the fixes undid another.

Check your understanding:
Which changes belong in environment values or overlays, which in shared templates, and which need controller logic?
