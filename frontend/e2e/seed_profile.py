"""Create explicit historical and measured-evidence fixtures in a disposable UI profile."""

import json
import sys
from pathlib import Path

from dockyard.models import Assessment, CheckStatus, Evidence
from dockyard.service import Service
from dockyard.store import timestamp

service = Service(Path(sys.argv[1]))
service.store.mark("m08-mission", "viewed", 1)
with service.store.connection() as connection:
    connection.execute("UPDATE progress SET practiced=1,demonstrated=1 WHERE unit_id='m08-mission'")
service.store.save_assessment(
    Assessment(
        id="ui-measurement-fixture",
        unit_id="m13-mission",
        revision=1,
        lab_id="ui-fixture",
        status=CheckStatus.FAIL,
        started_at=timestamp(),
        finished_at=timestamp(),
        file_digest="fixture",
        independent=True,
        evidence=[
            Evidence(
                criterion="capacity-scaling",
                title="CPU samples explain the scale decision",
                status=CheckStatus.FAIL,
                expected="true",
                observed="false",
                diagnostic="Wait for the replacement Pods to be measured.",
                details=json.dumps(
                    {
                        "desired_replicas": 4,
                        "measured_pods": ["dispatch-fixture-a", "dispatch-fixture-b"],
                    },
                    indent=2,
                ),
            )
        ],
    )
)
