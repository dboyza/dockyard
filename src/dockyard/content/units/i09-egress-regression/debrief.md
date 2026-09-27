# Recovery review

This incident combines missing UDP DNS egress with a worker queue rule targeting the wrong port.
Restoring name resolution alone can make the API appear recovered while background processing still fails.
The traffic matrix checks actual allowed and denied connections, then submits a job from the permitted frontend.
Equivalent narrow additive policies are accepted when they preserve the same live boundary.
Explain how a blanket allow-all rule could make the positive test pass while violating the recovery contract.
