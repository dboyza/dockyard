# Debrief: Restore a database onto independent storage

The restored records live on an independent destination claim while the source claim and its marker remain intact.
This distinguishes a successful restore from restarting the old database or merely producing a dump file.

## Explain your result

Which identities and data observations show that the recovered database is independent of the source storage?

## Transfer beyond this lab

A production recovery rehearsal must also measure recoverable data loss and recovery time, and keep a usable backup outside the original failure domain.
