## A clean stop is not an available service

Dispatch received SIGTERM, exited with code 0, and Docker kept its state and logs.
That is the right result for a deliberate shutdown, even though requests now fail.

Check your understanding:
How would the exit code and logs differ between a crash, a deliberate stop, and a program that simply had nothing more to do?
Which of those three would leave a web service unavailable?
