## Work that is supposed to finish

A web service is working when it keeps running.
A maintenance task is working when it *finishes* successfully.
Kubernetes has two controllers for finite work:

- A **Job** runs a task in one or more Pods until it succeeds, retrying failures up to a limit.
- A **CronJob** creates a new Job on a schedule.

## Job settings you need to know

- `backoffLimit` is how many times a failed attempt is retried before the Job gives up. Keep it small, so a broken task fails visibly instead of retrying forever.
- `restartPolicy` must be `Never` or `OnFailure` in a Job. `Never` starts a fresh Pod for each attempt, which keeps the failed Pods around for you to read their logs.
- A Job’s Pod template cannot be changed after the Job is created. To run a corrected task, delete the old Job and create a new one.
- `completions` is how many Pods must succeed for the Job to be complete (default 1), and `parallelism` is how many may run at once.
- `activeDeadlineSeconds` stops the whole Job, and marks it failed, if it runs longer than that many seconds.
- `ttlSecondsAfterFinished` deletes a finished Job, and its Pods, that many seconds after it ends.

For example, this Job runs five copies of a task, two at a time, gives up after two minutes, and cleans itself up an hour after finishing:

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: batch-import
spec:
  completions: 5
  parallelism: 2
  backoffLimit: 2
  activeDeadlineSeconds: 120
  ttlSecondsAfterFinished: 3600
  template:
    spec:
      restartPolicy: Never
      containers:
        - name: import
          image: busybox
          command: ["sh", "-c", "echo importing; sleep 5"]
```

`kubectl get job batch-import` shows progress in the `COMPLETIONS` column, such as `2/5`.

## Reading a cron schedule

A CronJob’s `schedule` uses the classic Linux **cron** format: five fields separated by spaces.

```text
┌──────── minute (0-59)
│ ┌────── hour (0-23)
│ │ ┌──── day of the month (1-31)
│ │ │ ┌── month (1-12)
│ │ │ │ ┌ day of the week (0-6, Sunday is 0)
│ │ │ │ │
* * * * *
```

`*` means “every”.
`*/5` in the minute field means “every 5 minutes”.
Some examples:

| Schedule | Runs |
| --- | --- |
| `*/5 * * * *` | every five minutes |
| `0 * * * *` | at the start of every hour |
| `17 2 * * *` | at 02:17 every day |
| `30 9 * * 1` | at 09:30 every Monday |

By default the time zone is the cluster’s, usually UTC.
You can set `timeZone: Etc/UTC` or another zone name on the CronJob to be explicit.
Always put quotes around the schedule in YAML, because `*` has a special meaning there.

## CronJob settings you need to know

- `concurrencyPolicy` decides what happens if a run is still going when the next one is due: `Allow` runs both, `Forbid` skips the new one, and `Replace` stops the old one and starts the new one.
- `suspend: true` pauses the schedule. Jobs already created keep running.
- `successfulJobsHistoryLimit` and `failedJobsHistoryLimit` control how many finished Jobs are kept for you to inspect.

A schedule does not guarantee a task runs exactly once: a run can be retried, or missed if the cluster is down.
Write maintenance tasks so running them twice does no harm.

## This lab

The `dispatch-maintenance` CronJob is suspended, and its command runs a script that does not exist.
The real script, `maintenance.py`, counts Dispatch’s jobs and records the count in a PostgreSQL table called `maintenance_runs`, one row per Job name.

You don’t have to wait five minutes to test a CronJob.
You can create a Job from its template straight away:

```sh
kubectl get cronjob dispatch-maintenance
kubectl create job maintenance-proof --from=cronjob/dispatch-maintenance
kubectl wait --for=condition=Complete job/maintenance-proof --timeout=90s
kubectl logs job/maintenance-proof
```

If `maintenance-proof` already exists from a failed attempt, delete it first with `kubectl delete job maintenance-proof`; fixing the CronJob does not change Jobs it already created.

To see the row the task wrote, run a query inside the database Pod:

```sh
kubectl exec deployment/db -- psql -U dispatch -d dispatch -c 'SELECT * FROM maintenance_runs;'
```

A log line saying “complete” is encouraging, but the row in the database is the real result.
Check work reads that table itself.

## Generate them quickly

```sh
kubectl create job once --image=busybox --dry-run=client -o yaml -- echo hello
kubectl create cronjob tidy --image=busybox --schedule="*/5 * * * *" --dry-run=client -o yaml -- echo tidy
```
