"""Rotate the practice database credential without writing it into source or process arguments."""

import base64
import json
import os
import secrets
import subprocess
import time
from pathlib import Path


def command(*args, data=None):
    result = subprocess.run(list(args), input=data, text=True, capture_output=True, timeout=180)
    if result.returncode:
        raise SystemExit(result.stderr or "The credential operation did not complete.")
    return result.stdout.strip()


def get(kind, name):
    return json.loads(command("kubectl", "get", kind, name, "-o", "json"))


private = Path(os.environ["DOCKYARD_STORAGE"])
private.mkdir(parents=True, exist_ok=True)
path = private / "next-database-password"
if path.is_symlink():
    raise SystemExit("The saved practice credential must be a private regular file.")
if not path.exists():
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w") as output:
        output.write(secrets.token_urlsafe(32))
next_password = path.read_text().strip()
if not next_password or any(
    c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-"
    for c in next_password
):
    raise SystemExit("The saved practice credential has an unexpected format.")
selector = get("service", "db")["spec"]["selector"]
pods = json.loads(
    command(
        "kubectl",
        "get",
        "pods",
        "-l",
        ",".join(k + "=" + v for k, v in selector.items()),
        "-o",
        "json",
    )
)["items"]
if len(pods) != 1 or pods[0].get("metadata", {}).get("deletionTimestamp"):
    raise SystemExit("Restore one active database target before rotating its credential.")
database_pod = pods[0]["metadata"]["name"]
# The supplied database role is a local practice administrator; production roles need a separate design.
command(
    "kubectl",
    "exec",
    "-i",
    database_pod,
    "--",
    "psql",
    "-U",
    "dispatch",
    "-d",
    "dispatch",
    "-v",
    "ON_ERROR_STOP=1",
    data="ALTER ROLE dispatch PASSWORD '" + next_password + "';\n",
)
secret = {
    "apiVersion": "v1",
    "kind": "Secret",
    "metadata": {"name": "dispatch-database", "namespace": "dispatch"},
    "type": "Opaque",
    "stringData": {"password": next_password},
}
command("kubectl", "apply", "-f", "-", data=json.dumps(secret))
for deployment in ("dispatch", "worker"):
    command("kubectl", "rollout", "restart", "deployment/" + deployment)
    command("kubectl", "rollout", "status", "deployment/" + deployment, "--timeout=150s")
probe = """import json,sys,psycopg
passwords=json.load(sys.stdin)
result={}
for name,password in passwords.items():
    try:
        with psycopg.connect(host="db",dbname="dispatch",user="dispatch",password=password,connect_timeout=3) as connection:
            connection.execute("SELECT 1")
        result[name]=True
    except psycopg.OperationalError: result[name]=False
print(json.dumps(result))
"""
observed = json.loads(
    command(
        "kubectl",
        "exec",
        "-i",
        "deployment/dispatch",
        "-c",
        "api",
        "--",
        "python",
        "-c",
        probe,
        data=json.dumps({"old": os.environ["DOCKYARD_DB_PASSWORD"], "new": next_password}),
    )
)
if observed != {"old": False, "new": True}:
    raise SystemExit("The old/new TCP authentication observations do not establish rotation.")
live_secret = get("secret", "dispatch-database")
if base64.b64decode(live_secret["data"]["password"]).decode() != next_password:
    raise SystemExit("The live credential no longer matches the observed rotation.")
record = {
    "lab": os.environ["DOCKYARD_LAB"],
    "database_pod_uid": pods[0]["metadata"]["uid"],
    "secret_uid": live_secret["metadata"]["uid"],
    "secret_revision": live_secret["metadata"]["resourceVersion"],
    "authentication": observed,
    "finished": time.time(),
}
Path("rotation-evidence.json").write_text(json.dumps(record, indent=2) + "\n")
print(json.dumps(record, indent=2))
