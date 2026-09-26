## Independent infrastructure recovery

Dispatch stopped completing jobs after a maintenance change.
The native guests still exist, but the frontend resolver behavior, worker forwarding setting, and database placement no longer match the intended design.
Use the actual layers to narrow the problem rather than applying every previous repair blindly.
The original database volume and a pre-incident sentinel must survive.

The trusted frontend belongs on the control plane and uses cluster DNS.
The API and database belong on the worker, where the CSI reference driver can mount the original volume.
Linux forwarding must permit Pod traffic to traverse that worker's network stack.
Observe each boundary separately, then verify the complete application path.

Write an infrastructure handoff describing the symptoms, hypotheses, observations, changes, and continuity proof.
The written handoff is self-reviewed; runtime checks establish actual behavior without claiming to judge the quality of your reasoning.
Keep credentials and raw administrative kubeconfigs out of the handoff.
