"""Restore into separate storage and switch the Service after verification."""

import base64
import hashlib
import json
import os
import subprocess
from pathlib import Path

from cryptography.hazmat.primitives.ciphers.aead import AESGCM


def command(*args, data=None):
    result = subprocess.run(args, input=data, capture_output=True, timeout=180)
    if result.returncode:
        raise SystemExit(result.stderr.decode() or "Restore operation failed.")
    return result.stdout


record = json.loads(Path("backup.json").read_text())
if record["schema"] != 1 or record["lab"] != os.environ["DOCKYARD_LAB"]:
    raise SystemExit("The backup belongs to a different lab or schema.")
key_path = Path(os.environ["DOCKYARD_STORAGE"]) / "backup.key"
if key_path.is_symlink():
    raise SystemExit("The backup key must be a private regular file.")
plaintext = AESGCM(key_path.read_bytes()).decrypt(
    base64.b64decode(record["nonce"]),
    base64.b64decode(record["ciphertext"]),
    ("dockyard-backup-v1:" + record["lab"]).encode(),
)
if hashlib.sha256(plaintext).hexdigest() != record["plaintext_sha256"]:
    raise SystemExit("The authenticated backup does not match its recorded digest.")
rendered = command("python", "render.py", "recovery.yaml")
command("kubectl", "apply", "-f", "-", data=rendered)
command("kubectl", "rollout", "status", "statefulset/db-recovery", "--timeout=150s")
command(
    "kubectl",
    "exec",
    "-i",
    "statefulset/db-recovery",
    "--",
    "psql",
    "-U",
    "dispatch",
    "-d",
    "dispatch",
    "-v",
    "ON_ERROR_STOP=1",
    data=plaintext,
)
# Verify the known data before directing application traffic to the restored database.
marker = record["marker"]["id"]
if len(marker) != 32 or any(c not in "0123456789abcdef" for c in marker):
    raise SystemExit("Unexpected marker identity.")
actual = command(
    "kubectl",
    "exec",
    "statefulset/db-recovery",
    "--",
    "psql",
    "-U",
    "dispatch",
    "-d",
    "dispatch",
    "-Atc",
    "SELECT row_to_json(j) FROM jobs j WHERE id='" + marker + "'",
)
if any(
    json.loads(actual)[k] != record["marker"][k]
    for k in ("id", "title", "status", "result", "worker")
):
    raise SystemExit("Restored row differs from the completed backup marker.")
command(
    "kubectl",
    "patch",
    "service",
    "db",
    "--type=merge",
    "-p",
    '{"spec":{"selector":{"app":"db","recovery":"restored"}}}',
)
for name in ("dispatch", "worker"):
    command("kubectl", "rollout", "restart", "deployment/" + name)
    command("kubectl", "rollout", "status", "deployment/" + name, "--timeout=150s")
print("Restored marker verified in separate storage. Database Service switched.")
