## Several kinds of work, one application

Dispatch now has four kinds of workload, each with the controller that suits it:

- the API, which must stay available;
- the workers, which process jobs and can scale;
- a node agent, which must run on every node;
- a maintenance task, which must run on a schedule and finish.

In this mission all of them are broken in some way.
There are no step-by-step commands; use what you learned in this module.
Take each controller in turn: look at what it asks for, what is actually running, and why they differ.

Remember that a list of green Pods is not the goal.
Submit a real job and watch it finish, and check the maintenance task’s row in the database.

## A limitation to write down

The database in this module still uses an `emptyDir` volume, so its data vanishes if the database Pod is replaced.
Part of your write-up is explaining when that would happen and what you would change next.

## Working on your own

Try it without hints first.
Hints and the reference solution are available, but using them marks this attempt as practice with help.
