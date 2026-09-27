# Recovery review

The process had started successfully; the readiness request was sent to the wrong port.
A failed readiness probe removes a backend without requiring the healthy process to restart.
A correct repair retains the readiness dependency check and restores Service traffic.
Explain which observation ruled out a slow startup and which observation ruled out a database failure.
