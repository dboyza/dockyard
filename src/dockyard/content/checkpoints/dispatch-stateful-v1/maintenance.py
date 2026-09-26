"""Record an actual database maintenance observation from a finite Job."""
import json
import os
from database import database, initialize

with database() as connection:
    initialize(connection)
    connection.execute("CREATE TABLE IF NOT EXISTS maintenance_runs (name TEXT PRIMARY KEY, jobs INTEGER NOT NULL, observed_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP)")
    total = connection.execute("SELECT count(*) AS total FROM jobs").fetchone()["total"]
    name = os.environ["JOB_NAME"]
    connection.execute("INSERT INTO maintenance_runs(name,jobs) VALUES(%s,%s) ON CONFLICT(name) DO UPDATE SET jobs=EXCLUDED.jobs,observed_at=CURRENT_TIMESTAMP", (name,total))
    print(json.dumps({"maintenance": "complete", "job": name, "jobs": total}), flush=True)
