## Your own object type, reconciled

The CRD taught the API a new word.
The WorkerPool said what you wanted.
The controller made it happen, and kept it that way when the Deployment was changed by hand.

Check your understanding:
Follow one change from `kubectl edit workerpool dispatch` to new worker Pods.
Why is a status that says Ready not trustworthy if its `observedGeneration` is lower than the object’s `generation`?
