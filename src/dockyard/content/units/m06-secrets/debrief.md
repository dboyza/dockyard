## What changed

The signing step still read the token, but from a file BuildKit mounted for that one step, so the layer and the history kept only the command.
A build argument is recorded with every `RUN` step that uses it, which is why the old image carried the token in plain sight.

Check your understanding: if you change only `release-token.txt` and rebuild, why might `SIGNATURE` not change, and what would you do about it?
Where else besides the image history could a secret passed with `ENV` end up?
