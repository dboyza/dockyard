## Compare your diagnosis

The incident changed an existing file to owner-read-only after data had already been written.
Health and read paths continued working, which made process-level monitoring misleading.
Restoring the owner write bit repaired the narrow permission boundary while retaining the data and non-root runtime.
Broad permissions or replacing the database would violate the preservation and access constraints.

Which observation ruled out your first alternative explanation?
Which preservation constraint would a quick reset have violated?
What should an operator monitor to detect this failure earlier?
