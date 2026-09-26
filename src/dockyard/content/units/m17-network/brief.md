# Repair the intended network boundary

The business-read policy has split its namespace and Pod selectors into alternative peers, and the DNS rule permits only UDP.
Repair those two faults in network.yaml while preserving the default-deny baseline and required dependency rules.
Render and apply the policy file, then inspect the measured allowed and denied connections.
The trusted frontend must reach the API across nodes; an untrusted frontend and the same trusted label in the wrong namespace must not.
Both DNS protocols must work, frontend-to-database access must fail, and the API must be unable to reach the independent egress target that remains reachable from the frontend.
