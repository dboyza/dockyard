## Bound is not the same as usable

The claim was Bound the whole time; the problem was running the database on a node that could not reach its data.
Putting it back on the worker let the original volume attach and mount, with its data intact.

Check your understanding:
Which step in the CSI chain would have failed if the driver were not registered on the worker?
Why could you delete the `db-0` Pod safely, but not its claim?
