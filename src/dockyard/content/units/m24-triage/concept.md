## Triage: find the broken step, then fix only that

**Triage** means working out quickly what is broken and what matters most, before you change anything.
When several things fail at once, it is tempting to try every fix you know.
That often makes things worse, and afterwards nobody can say which change helped.

A calmer approach is a short loop:

1. **Observe** the symptom, in words a user would use.
2. **Guess** one cause that would explain it.
3. **Test** that guess with a command whose answer would prove it right or wrong.
4. **Change** one thing, if the test supports the guess.
5. **Check** whether the symptom changed.

If the test disagrees with your guess, change the guess, not the cluster.
Write each loop down in a line or two; it becomes your handoff later.

## Follow the request through each step

A Dispatch job only succeeds if every step works:
the request reaches the API through its Service, the API stores the job, a worker picks it up, and the result is saved in PostgreSQL.
A healthy API Pod proves only the second step.
So test the steps in order, and do not stop at the first one that looks fine.

## Worked example

In this lab, users report that Dispatch is not working.
Start with the route into the API:

```sh
kubectl get deployment dispatch worker
kubectl get service dispatch -o jsonpath='{.spec.selector}'; echo
kubectl get pods -l app=dispatch --show-labels
kubectl get endpointslices -l kubernetes.io/service-name=dispatch
```

Compare the Service's selector with the Pods' labels.
If no running Pod has every label in the selector, the Service has no endpoints and sends requests nowhere, however healthy the Pods are.
The Pods' `track` label tells you which release they belong to; the working one is `stable`.

You can also try the route the way a user would.
`$DOCKYARD_PORT` is the lab's own port for the Dispatch page, which goes through this Service:

```sh
curl -s http://127.0.0.1:$DOCKYARD_PORT/readyz
```

An empty reply or an error means requests are not reaching the API.
You can also open `http://127.0.0.1:PORT` in a browser, using the number `echo $DOCKYARD_PORT` prints.

Fixing one fault can reveal another that the first one hid.
Once requests reach the API, submit a job and watch its status:

```sh
curl -s -X POST -H 'Content-Type: application/json' -d '{"title":"triage-test"}' http://127.0.0.1:$DOCKYARD_PORT/jobs
curl -s http://127.0.0.1:$DOCKYARD_PORT/jobs
```

If the job stays `queued`, the API is fine and the problem is further along, so look at the workers:

```sh
kubectl get deployment worker
kubectl logs deployment/worker --tail=20
```

A Deployment with `0/0` ready has been scaled to zero on purpose, which is different from Pods that crash.

Make the smallest change that fixes each step, for example `kubectl patch` for a selector or `kubectl scale` for replicas.
Re-running every setup script would also "work", but in a real incident it could overwrite other people's changes.
Leave the database and the queue alone; nothing is wrong with them.

## Close the loop

The incident is over when a new job reaches `done` and its result is saved, and the job stored before the incident is still there.
Check work sends real jobs through both the private browser path and the trusted frontend on the other node.

The same habits help in the exams: read the whole task, check your context and namespace, fix only what is asked, and check the result before moving on.
The exam technique guide in the reference section has more.
