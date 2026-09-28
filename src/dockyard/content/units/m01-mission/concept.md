## The launch said it worked, but Dispatch is missing

Someone changed the command used to start Dispatch.
The launch reported success, yet the API never answered a request.
Your job is to find out why and put it right, using what you learned in this module.

This is a **mission**: it describes the result you need, not the commands to type.
Take it one question at a time:

- What state is the container in, and what exit code did it report?
- What command did it actually run?
- What did that command print in the logs?

Remember from the last lesson that `Exited (0)` only means the program finished without an error.
For a web service, finishing at all is the problem.

## Working on your own

Try the task without hints first.
Hints and the reference solution are there if you get stuck, but using them marks this attempt as practice with help.
Any commands that produce the working result are accepted.
