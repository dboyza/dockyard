## Compare your diagnosis

The archiver required a node labeled for a `cold` storage tier, and no node had that label.
With nothing to schedule, the claim waited for its first consumer forever.
Pointing the archiver at the existing `warm` tier let the Pod schedule, and the claim was bound and provisioned on that node.

Check your understanding:
Which event showed the problem was scheduling, not storage?
Why would switching to an `emptyDir` have looked like a fix, while failing the real requirement?
