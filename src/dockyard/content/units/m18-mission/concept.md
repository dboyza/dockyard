# Harden and recover Dispatch

This capstone joins artifact evidence, service credentials, enforced connectivity, and independent data recovery.
The starting environment contains an unused vulnerable dependency, an original database password, a stopped primary database, and a frontend policy aimed at a retired client label.
An authenticated backup was taken before the compound failure.

Use observations to choose the order of work.
An unavailable database and blocked frontend can both cause an application symptom, but they require different repairs.
Inspect Pods, Service selectors, policy peers, and backup metadata before assuming a single root cause.
Keep the original volume available while validating the recovered database.

The release is complete when the unused vulnerable component is absent from the current image and actual consumers, the old credential is rejected while the current one succeeds, the authenticated backup is served from separate storage, and a new frontend job finishes correctly.
Retain the before and after reports as evidence with their database date.
A passing exercise does not dismiss remaining image findings or substitute for a production security review.

Prepare a short operator handoff describing the failure chain, remediation order, verified observations, remaining risks, and next recovery drill.
Include the original and restored volume identities and explain how you would reverse the traffic switch without overwriting either copy.
Your work should make the next operator's decisions clear without exposing credentials.
