## Let the API displace batch work

Overnight report rendering has filled the node, and one of the two Dispatch API replicas cannot start.

1. Find the Pending API Pod, read why in its Events, and compare the Pods' priorities.
2. Create `priority.yaml` with a PriorityClass whose value is higher than `batch-low`'s 1000, with `globalDefault: false`.
3. Give the `dispatch` Deployment's Pod template that `priorityClassName`.
4. Run `sh run.sh`, watch one batch Pod make way, and choose **Check work**.

Do not scale or delete `report-batch`, and keep each API container's request of one slot.
In your notes, explain where the displaced batch Pod went, and what would bring it back.
