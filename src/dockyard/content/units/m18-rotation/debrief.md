## New password in, old password out

PostgreSQL now rejects the old password, and the API and worker are using the new one.

Check your understanding:
Why do you need both a successful new login and a rejected old one?
If both passwords failed, what would you check before concluding anything?
