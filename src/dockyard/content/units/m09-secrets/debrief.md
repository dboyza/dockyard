# Debrief: Deliver a credential through a Secret

The repaired application reads its projected password file and authenticates against the real database.
This proves the key reference, mount permissions, and consumer behavior together, while a Secret object by itself would prove none of those connections.

## Explain your result

Explain why base64 encoding does not protect a value from someone authorized to read the Secret, and where this credential could leak during troubleshooting.

## Transfer beyond this lab

Coordinate database-side rotation with client refresh, and keep live credentials outside exported source and operational notes.
