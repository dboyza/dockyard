# Prove promotion, drift repair, and recovery

The starting release is healthy, but no promotion or recovery evidence exists.
Read delivery-proof.py, then run python gitops.py wait followed by python delivery-proof.py.
Inspect each Git commit rather than treating the script's final message as the result.
Explain why the same digest reaches staging, why Flux repairs a manual scale change, and why recovery uses a Git revert.
Leave dispatch-3 serving in both release targets, with the failed candidate and recovery preserved in history.
