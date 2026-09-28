## Make the latency signal useful and prove the alert

1. In `dashboard.json`, fix the latency panel so it shows the fraction of `/jobs` reads slower than 250 ms. It currently uses a metric that does not exist.
2. In `rules.yaml`, fix the alert so it fires when that same fraction is above 10% for fifteen seconds. Keep its `warning` severity and its summary and runbook annotations.
3. Run `sh monitoring.sh`, then `python alert-proof.py`.
4. Open the dashboard and read `alert-evidence.json`.
5. Choose **Check work**.

Do not raise the threshold, remove the alert, or treat missing data as zero.
