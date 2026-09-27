# Debrief: Compare stable and candidate releases

The shared Service selects both stable and candidate Pods, while the preview Service selects only the candidate release.
Release responses establish which artifact the client reached rather than relying on desired image fields alone.

## Explain your result

Explain why the ratio of stable to candidate Pods is not an exact traffic-weighting guarantee.

## Transfer beyond this lab

Use a routing system with explicit traffic policy when a production release requires controlled request proportions or consistent user cohorts.
