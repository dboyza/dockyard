# Make the observation actionable

Repair the latency panel in dashboard.json to show the fraction of GET /jobs reads slower than 250ms.
The current query refers to a nonexistent metric.
Repair the alert rule in rules.yaml so that the same slow fraction above 10 percent remains true for fifteen seconds before firing.
Keep the warning severity and useful summary/runbook annotations.
Apply both configurations with `sh monitoring.sh`, then run `python alert-proof.py`.
The rehearsal must observe real firing and subsequent recovery while restoring the fast delay.
Inspect the dashboard at the assigned loopback address and the contents of alert-evidence.json.
Do not lower the SLO, remove the alert, or treat missing data as zero.
