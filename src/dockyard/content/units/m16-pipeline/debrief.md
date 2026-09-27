# Debrief: Gate a local image publication

The local pipeline gates publication on observed build and application behavior before placing an artifact in the registry.
An immutable image digest identifies the published artifact more precisely than a mutable tag.

## Explain your result

Which failed gate should prevent publication, and how would you prove the running workload uses the artifact that passed those gates?

## Transfer beyond this lab

Production delivery adds independently protected credentials and provenance verification, while retaining the same separation between building, validating, and promoting.
