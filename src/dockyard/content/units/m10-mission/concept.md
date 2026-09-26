# Mission: a route is an end-to-end contract

The same healthy application can be unreachable through several independently broken paths.
Treat each request as a chain of concrete destinations rather than assuming that one green resource establishes the whole system.
Use the previous lessons to separate address allocation, route attachment, Service selection, port translation, certificate identity, and application response.

Your evidence should identify which client sent each request and what network it could reach.
A Docker-network LoadBalancer address is meaningful to the supplied external client; the Mac uses explicit loopback port mappings.
For TLS, keep the hostname and certificate verification intact.
For Gateway API, confirm current conditions and reject unmatched hostnames.
