# Separate release existence from pull authority

An image existing in a registry does not authorize every node to retrieve it.
A developer's Docker login also does not automatically configure Kubernetes workload credentials.
Read the Pod's pull error and compare its exact image registry authority with the Secret's auths key.
The Secret must be available in the Pod's namespace and referenced by the Pod or its ServiceAccount.
For a separate example, credentials for `registry.example:5443` do not automatically identify `registry.example:5000` as the same authority.

This incident uses an authenticated registry on an owned local Docker network with a host loopback endpoint.
The supplied kind nodes have an explicit mirror route to that owned registry.
That local HTTP transport is a teaching convenience inside the owned environment; a remote registry needs appropriate TLS and credential handling.
The registry retains authentication throughout the repair.
Always pull policy makes new Pods resolve the release with their current identity even when underlying image layers are cached.
