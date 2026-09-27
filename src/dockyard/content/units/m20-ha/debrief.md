# Debrief: Keep the API writable through a control-plane outage

The primary API server and etcd member remain stopped while the surviving members retain the original three-member voting configuration.
A fresh API write demonstrates both usable client routing and surviving quorum, while the application job adds a cross-node data-path observation.

## Explain your result

Why can a healthy etcd majority coexist with a broken client endpoint, and why would deleting the failed member change the scenario you were asked to recover?

## Transfer beyond this lab

This local topology teaches routing and quorum mechanics, but all guests still share one host computer and the endpoint itself has additional failure boundaries.
