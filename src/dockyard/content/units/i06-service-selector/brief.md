# Incident report

A release-label change leaves two ready replicas and working Pod addresses, while requests to the stable Service stop connecting.

Restore the existing stable Service to exactly the two ready Dispatch API replicas.
Retain the Service name and port, the database claim, and the original job.
Show a fresh request that completes through the API and worker.
Do not hand-author EndpointSlices or bypass the Service with a Pod address.

Write a short account of the first discriminating observation, the repair, and a regression check.
Use the debrief as a self-review rubric; prose is not automatically graded.
