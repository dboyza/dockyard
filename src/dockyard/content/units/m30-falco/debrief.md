## What changed

Falco now watches the worker's system calls and alerts, with the namespace and Pod, whenever a shell starts in an application container.
Its first alerts pointed at `report-sync` in `billing`, which starts a shell every fifteen seconds.
Whether that is a design flaw or something worse is the next question to answer.

Check your understanding: an attacker who gets into a Dispatch container avoids shells and uses Python directly.
Which of Falco's default rules, or which rule of your own, could still catch them?
Why should a rule's output name the Pod, not just the process?
