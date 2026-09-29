## Restore traffic between the nodes

1. Find where the frontend and the API run, and confirm a request from the frontend to the API Pod IP fails.
2. On the control-plane VM, find the rule that drops VXLAN traffic and watch its counter rise when you retry.
3. Delete only that rule.
4. Choose **Check work**.

Keep the frontend on the control plane and the API on the worker, and leave every other firewall rule alone.
In your notes, explain which observations told process health apart from packet delivery.
