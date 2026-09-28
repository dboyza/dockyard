## What did the final stage leave behind?

Your final container can read its application files and answer requests without running as root.
It does not contain the first stage’s `/source` directory.

Point to the Dockerfile instruction that copies files between stages and the instruction that selects the running user.
Predict what would happen if you copied the whole first-stage filesystem into the final stage.
Two `FROM` lines alone do not guarantee that build-only files stay out.
