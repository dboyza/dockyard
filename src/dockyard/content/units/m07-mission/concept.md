## Your first Kubernetes mission

This mission brings together the three lessons in this module.
Dispatch should run as two copies behind its Service, but right now it doesn’t.
There are no step-by-step commands; use what you have learned to find each problem and fix it.

A good way to work:

1. Check your context and namespace.
2. Look at the Deployment: how many copies does it ask for, and how many are running?
3. Look at the Service: which labels does it select, and does it have endpoints?
4. Fix the files, apply them, and confirm with a real request through the Service.

Keep your fixes in the workspace files, not just in the live cluster, so someone else could apply them again.

## Working on your own

Try it without hints first.
Hints and the reference solution are available, but using them marks this attempt as practice with help.
When you pass, Dockyard saves your manifests and notes as a portfolio checkpoint, leaving out credentials.
