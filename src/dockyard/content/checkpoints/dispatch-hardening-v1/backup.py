"""Encrypt a consistent logical backup, then rehearse losing the primary process."""

import base64
import hashlib
import json
import os
import secrets
import subprocess
import time
import uuid
from pathlib import Path

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from dockyard.probes.security import request


def command(*args, data=None):
    result = subprocess.run(args, input=data, capture_output=True, timeout=180)
    if result.returncode:
        raise SystemExit(result.stderr.decode() or "Backup operation failed.")
    return result.stdout


private = Path(os.environ["DOCKYARD_STORAGE"])
private.mkdir(parents=True, exist_ok=True)
key_path = private / "backup.key"
if key_path.is_symlink():
    raise SystemExit("The backup key must be a private regular file.")
if not key_path.exists():
    descriptor = os.open(key_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "wb") as target:
        target.write(AESGCM.generate_key(bit_length=256))
key = key_path.read_bytes()
marker = "recovery-" + uuid.uuid4().hex
job = request("/jobs", {"title": marker}, "POST")
deadline = time.monotonic() + 30
while time.monotonic() < deadline:
    jobs = request("/jobs")
    rows = jobs if isinstance(jobs, list) else jobs.get("jobs", [])
    row = next(
        (item for item in rows if item["id"] == job["id"] and item["status"] == "done"), None
    )
    if row:
        break
    time.sleep(0.3)
else:
    raise SystemExit("The marker job did not complete before backup.")
source = json.loads(command("kubectl", "get", "pvc", "data-db-0", "-o", "json"))
plaintext = command(
    "kubectl",
    "exec",
    "statefulset/db",
    "--",
    "pg_dump",
    "-U",
    "dispatch",
    "-d",
    "dispatch",
    "--clean",
    "--if-exists",
    "--no-owner",
    "--no-acl",
)
aad = ("dockyard-backup-v1:" + os.environ["DOCKYARD_LAB"]).encode()
nonce = secrets.token_bytes(12)
ciphertext = AESGCM(key).encrypt(nonce, plaintext, aad)
tampered = ciphertext[:-1] + bytes([ciphertext[-1] ^ 1])
try:
    AESGCM(key).decrypt(nonce, tampered, aad)
except InvalidTag:
    rejected = True
else:
    raise SystemExit("An altered authentication tag was accepted.")
record = {
    "schema": 1,
    "lab": os.environ["DOCKYARD_LAB"],
    "nonce": base64.b64encode(nonce).decode(),
    "ciphertext": base64.b64encode(ciphertext).decode(),
    "plaintext_sha256": hashlib.sha256(plaintext).hexdigest(),
    "marker": row,
    "source_pvc_uid": source["metadata"]["uid"],
    "source_volume": source["spec"]["volumeName"],
    "tamper_rejected": rejected,
    "at": time.time(),
}
Path("backup.json").write_text(json.dumps(record, indent=2) + "\n")
command("kubectl", "scale", "statefulset/db", "--replicas=0")
command("kubectl", "wait", "--for=delete", "pod/db-0", "--timeout=120s")
print("Encrypted backup saved. Original volume retained; primary process stopped.")
