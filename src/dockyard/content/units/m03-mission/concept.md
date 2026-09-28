## Make the service relationship work from scratch

You now know how to build an image, publish an API port, connect containers, and diagnose a dependency address.
This mission starts with source files rather than a prepared connection.
Use those skills to create one public entry point on your computer and one internal service.

The supplied image can run in either role.
The dependency’s health response includes its container identity, so you can check that the API really called that peer.
Keep the services connected by a name, not by an IP address observed during setup.

Plan the request path before running commands: your terminal to the API’s published port, then the API to the dependency over the shared bridge.
Check each part separately if the complete request fails.
