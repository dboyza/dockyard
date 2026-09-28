## History you can trust

The same tested digest moved from development to staging, a bad candidate failed without taking staging down, and a revert commit restored the good declaration.

Check your understanding:
How did you tell apart a change Flux had not applied yet from one it applied that then failed?
Why is reverting in Git not a complete rollback if the bad release had changed the database?
