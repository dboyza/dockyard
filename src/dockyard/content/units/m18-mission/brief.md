## Recover and harden Dispatch

Using the helpers from this module (`scan.py`, `build.json` with `repair-image.sh`, `rotate.py`, and `restore.py`), bring Dispatch back and harden it as described in Understand.
The network fault was made directly in the cluster: compare the live policies with `network.yaml` and put the intended policy back.
Decide the order yourself, and check each step before the next.

Write `handoff.md` for the next operator.
Say what failed and why, the order you fixed things in, what you checked, and the remaining risks.
Give the original and restored volume names, and explain how you would switch the database Service back without overwriting either copy.
Keep passwords and keys out of it.
