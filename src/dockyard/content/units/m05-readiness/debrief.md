Startup dependency order and readiness are now separate, explicit properties.
The observed workflow still matters after health checks pass, because a narrow health check cannot prove every user operation.
Describe what will happen if the database later becomes unavailable and which component is responsible for retrying.
