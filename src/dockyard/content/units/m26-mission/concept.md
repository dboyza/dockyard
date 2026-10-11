## An access review of your own

A security review has listed three ways this cluster grants more access than it should.
Closing them is your job, from confirming each finding to proving it is fixed with the API server's own answers.

Use what this module taught: unauthenticated requests and the authentication configuration, ServiceAccount tokens, and `kubectl auth can-i` with impersonation.
The details differ from the lessons, so investigate before you change anything, and expect one fix to touch the control plane.

## Working on your own

Try it without hints first.
Hints and the reference solution are available, but using them marks this attempt as practice with help.
Check work tests the live cluster; your report is for your own review against `report-rubric.md`.
