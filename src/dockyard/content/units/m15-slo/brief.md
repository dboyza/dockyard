# Measure, repair, and measure again

The business-read delay is 600ms while readiness remains healthy.
Run `python measure-slo.py before` and inspect the good-event ratio and individual request IDs.
Repair delay_ms to 20 in settings.yaml, render/apply it, restart the API, and wait for rollout.
Run `python measure-slo.py after`.
Keep the 95 percent objective and 250ms threshold in slo.json.
Explain why a successful readiness probe did not establish the latency target.
Record the sample size and scope so the twenty-request rehearsal is not mistaken for a production service-level report.
