## The release capstone

This mission brings together the three release lessons with everything before them.
Dispatch now has persistent storage, configuration, workers, and an API, and several release problems at once:

- the stable Deployment points at a bad image;
- its probes are wired to the wrong addresses;
- its rolling update settings could drop below the required capacity;
- the candidate preview does not work.

Work on one problem at a time, and check each fix before moving on.
Get the stable release healthy first; only then look at the candidate.

There are no step-by-step commands.
The earlier lessons’ inspection commands all still apply: `rollout history`, `describe pod`, EndpointSlices, and requests through each Service.

## Working on your own

Try it without hints first.
Hints and the reference solution are available, but using them marks this attempt as practice with help.
When you pass, Dockyard saves your manifests and runbook as a portfolio checkpoint.
