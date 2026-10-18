## Get the archiver running on its claim

Find out why the `archive` claim and the `archiver` Pod are stuck, and fix the cause.

- Keep the `archive` claim, its `standard` StorageClass, and its wait-for-consumer behavior.
- Run one `archiver` replica with the claim mounted at `/archive`, on a suitable node.
- Keep Dispatch’s namespace, database claim, and stored job.
- A new file written through the archiver’s mount must be readable by a separate Pod using the same claim.
- Do not replace the claim with an `emptyDir` or a folder on the node.

In your notes, record which event made you look at scheduling rather than at the storage provisioner.
