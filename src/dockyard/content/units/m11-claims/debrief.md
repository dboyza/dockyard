# Debrief: Connect claims to durable database storage

The database writes through a bound claim into the backing PersistentVolume, and a replacement Pod reads the original marker.
The marker makes persistence observable across Pod replacement instead of relying on a healthy-looking database process.

## Explain your result

Trace the data directory through the mount, claim, volume, and backing storage, naming which identities changed when the Pod was replaced.

## Transfer beyond this lab

This node-local volume survives the tested Pod lifecycle, but deleting the entire kind cluster removes its storage.
