## Measure, fix, and measure again

Dispatch waits 600 ms on every business read, while its readiness probe stays healthy.

1. Run `python measure-slo.py before` and look at the good fraction and the individual request IDs.
2. Change `delay_ms` to `20` in `settings.yaml`, apply it, restart the API, and wait for the rollout.
3. Run `python measure-slo.py after`.
4. Choose **Check work**.

Keep the 95% objective and the 250 ms threshold in `slo.json`.
In your notes, explain why a healthy readiness probe did not show the latency target was met, and record the sample size and scope of your measurement.
