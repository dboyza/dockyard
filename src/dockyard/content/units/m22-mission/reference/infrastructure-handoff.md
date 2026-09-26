# Infrastructure recovery handoff

The worker forwarding setting, trusted frontend DNS policy, and database placement were corrected.
The frontend again reaches an API Pod on the other node, and a new Service resolves and routes correctly.
The database uses its original CSI claim, volume handle, and worker mount.
The pre-incident SQL row remains, and a fresh Dispatch transaction completes.
The CSI reference driver stores data on one worker and does not replicate it or provide shared storage.
Host, endpoint, and storage redundancy remain separate production design work.
