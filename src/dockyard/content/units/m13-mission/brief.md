## Fix the capacity setup, then drain a worker

1. Fix the API’s required affinity and taint toleration in `platform.yaml`, the HPA target in `autoscale.yaml`, and `minAvailable` in `capacity.yaml`.
2. Keep the two dedicated workers, the API’s real requests and limits, the namespace budgets, the 2 to 4 HPA range, and the spread rule.
3. Wait for four available stable API replicas under the supplied load.
4. Run `python drain-proof.py`, then read its output and the new Pod distribution.
5. Choose **Check work**.

If the drain is blocked, find out why from the budget and placement; do not add force options or delete the budget.
Write a maintenance note.
Say which node you drained, what the samples showed, which Pods were replaced, and how much capacity remained.
Explain why these three nodes on one computer are not independent failure domains.
Keep the database’s storage and its placement unchanged throughout.
