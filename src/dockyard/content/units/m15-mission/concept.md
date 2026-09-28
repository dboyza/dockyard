## A slow service and broken monitoring

Dispatch is Ready, but its reads have become slow.
At the same time, the monitoring that should have caught it is broken in three places:
Prometheus is not finding the API Pods, a dashboard query returns nothing, and the latency alert has been replaced with an expression that can never fire.

This mission brings together the module.
Measure the problem *before* fixing anything, so you have evidence of what users experienced.
Then repair the monitoring and the service, prove the alert works, and measure again.

There are no step-by-step commands.
The scripts from the lessons all still apply: `measure-slo.py`, `monitoring.sh`, and `alert-proof.py`.

## Working on your own

Try it without hints first.
Hints and the reference solution are available, but using them marks this attempt as practice with help.
Check work reads the evidence files and the live system; your written diagnosis is for your own review.
