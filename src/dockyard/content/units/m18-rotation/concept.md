## Changing a password everywhere it is used

Passwords and keys should be replaced regularly, and immediately if one may have leaked.
This is **credential rotation**, and it involves more than editing a Secret:

1. The **server**, here PostgreSQL, must accept the new password and stop accepting the old one.
2. Every **consumer**, here the API and the worker, must start using the new password.

Changing the Secret alone does not change what PostgreSQL accepts.
Changing PostgreSQL alone breaks every consumer still holding the old password.
And consumers do not always notice a changed Secret: environment variables are fixed when a container starts, and even mounted files may be cached by the application.
So rotation is planned as separate steps, with a restart of the consumers.

```figure
rotation-steps
```

Some systems accept two passwords for a while, so consumers can switch over with no interruption.
This practice database only has one, so rotating it causes a short interruption.

Remember from the Secrets lesson that a Secret is only base64 encoded, and it can leak through Git history, terminal output, logs, or backups.

## This lab’s helper

`rotate.py` does the whole sequence without ever putting the password in a command line, a file in your workspace, or its output:

1. generates a new password;
2. changes it in PostgreSQL, sending the SQL through standard input;
3. updates the Kubernetes Secret, also through standard input;
4. restarts the API and worker.

It keeps a private copy of the new password outside your workspace, readable only by you.
Read it to see the order of operations.

```sh
python rotate.py
kubectl rollout status deployment/dispatch
kubectl rollout status deployment/worker
```

## Proving the rotation worked

You need two results against the **same, reachable** database:

- the **new** password logs in successfully;
- the **old** password is rejected.

If the database were down, both would fail, and that would prove nothing about the old password.
Check work does both attempts and then runs a real job.

The database account here is an administrator, which is fine for a disposable practice lab.
Real systems separate the application’s account from the one used to change schemas and manage credentials, and add encrypted connections and storage encryption, which are separate protections.

If PostgreSQL has the new password but a consumer did not restart properly, fix the consumer so it uses the new password; do not print passwords to compare them.
