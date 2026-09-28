## An alert you have seen fire

Your dashboard and alert now measure the same thing: the share of reads slower than 250 ms.
The rehearsal showed the alert firing when Dispatch was slow and clearing when it recovered.

Check your understanding:
Why would an alert on average latency miss a problem affecting one request in ten?
What would you see on the dashboard if Prometheus stopped scraping Dispatch, and how is that different from a quiet, healthy service?
