## Selectors connect, names don’t

The Service was looking for Pods labeled `app=dispatch-old`.
No Pod had that label, so its endpoint list stayed empty and requests had nowhere to go.
Changing the selector to match the Pods’ real label fixed it without touching the Pods.

Check your understanding:
Which single command would have shown you the problem fastest?
If a stray Pod from another app also had the label `app=dispatch`, what would happen to Dispatch’s traffic?
