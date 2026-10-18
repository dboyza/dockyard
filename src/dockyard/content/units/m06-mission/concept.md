## The Docker capstone

This mission brings together everything from the first six modules.
You will be handed a running but broken Dispatch project.
Your job is to fix it, ship it properly, lock it down, prove you can recover its data, and write instructions for the next person.

Here is the situation:

- The API answers, and the database holds an original job named `capstone-$DOCKYARD_LAB`.
- Background jobs are not finishing. The workers’ settings were changed in the last release.
- The project currently builds its image locally rather than running a published release.

There are no step-by-step commands.
Take it in stages and check each one before moving on.

## Stage by stage

1. **Diagnose the workers.** Follow a job from the API to the workers’ logs and compare their settings with the API’s, as in the Compose incident.
2. **Publish a release.** Build the image, push it to this lab’s registry, and find its digest, as in the registry lesson.
3. **Run by digest.** Point both the `api` and `worker` services at the digest reference with `image:`, and remove their `build:` sections so Compose runs the published release.
4. **Lock down the application.** Add the Compose restrictions from the previous lesson to `api` and `worker` only. PostgreSQL has to write its data, so leave the database’s settings alone.
5. **Prove recovery.** Back up the `dispatch` database with `pg_dump`, create a separate database called `restored`, and load the backup into it, as you practised when scaling workers. Then find the original job there. Leave the live `dispatch` database untouched.
6. **Hand over.** Write `RUNBOOK.md`.

## Writing the runbook

Write `RUNBOOK.md` for a colleague who did not watch you work.
Your runbook should explain how to start the project and check that it is healthy.
It should say what was broken and how you fixed it.
It should also cover backup and restore, and how to stop and resume without losing data.
Check work only confirms that the file exists and is not almost empty; how clear and complete it is is for you to judge.

## Working on your own

Try each stage without hints first.
Hints and the reference solution are available, but using them marks this attempt as practice with help.
When you pass, Dockyard saves a copy of your project files as a portfolio checkpoint.
It leaves out data, passwords, and other secrets.
