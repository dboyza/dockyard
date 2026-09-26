# Native operations handoff

The CRI client selected a retired Unix socket while the runtime itself remained active.
The worker kubelet service was stopped, so surviving containers were not proof of continuing node reconciliation.
The guest operator client selected the wrong API port even though the host client still authenticated successfully.
The repair restored the CRI endpoint, started kubelet, and installed a private working guest client.
Current leases, Ready conditions, running static components, verified trust, and a new persisted job establish the repaired boundaries.
Repeat these observations after resume; retained local database storage remains tied to one worker and does not provide replicated availability.
