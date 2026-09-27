# Debrief: Promote and recover a declared release

Promotion changes the declared release, while recovery restores a known working declaration and waits for the resulting behavior.
A reverted commit is not the end of recovery until the reconciler and the application have both converged.

## Explain your result

Explain how you distinguished an unapplied repository change from an applied release that failed readiness.

## Transfer beyond this lab

Review data compatibility and external dependencies before treating Git reversion as a complete production rollback.
