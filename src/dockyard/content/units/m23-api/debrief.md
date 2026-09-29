## What you did

The API server was pointed at a port where nothing listened, so every attempt to start ended with a refused connection to etcd.
You found that from the node, using `crictl` and the container's log, because kubectl could not reach the API at all.
Correcting one flag in the static Pod manifest was enough; the kubelet restarted the API server by itself.

## Check your understanding

- How did the log tell you this was a wrong address rather than a certificate problem?
- Why was running kubectl again and again never going to find the cause?
- If the manifest had a YAML mistake instead, where would you have looked?

## Beyond this lab

Keep a written procedure for reaching control-plane nodes when the API is down, and make sure the access it needs does not depend on the API itself.
