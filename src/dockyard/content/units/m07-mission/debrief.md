## The whole path, from name to Pod

You fixed two separate problems: the Deployment asked for no copies, and the Service looked for the wrong label.
Fixing only one would have left Dispatch unreachable.

Check your understanding:
Draw the path of a request from `http://dispatch:8080` to a Dispatch container, and name the command that shows each step working.
Which fix would a `kubectl get endpointslices` check have pointed you to first?
