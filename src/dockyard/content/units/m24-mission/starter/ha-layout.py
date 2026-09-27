"""Place cross-node diagnostic clients on a surviving control-plane guest."""

from pathlib import Path
from dockyard.native import current

runtime = current()
if len(runtime.discover()) != 4:
    raise RuntimeError("The HA layout requires three control planes and a worker")
path = Path("clients.yaml")
path.write_text(
    path.read_text().replace("${DOCKYARD_CONTROL_PLANE}", "${DOCKYARD_NODE_PREFIX}-cp2")
)
