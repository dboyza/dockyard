"""Observe drift repair, digest promotion, failed image pull, and a Git revert."""
import json
import os
import time
from pathlib import Path
import yaml
from gitops import command, commit, deploy, git, wait

wait()
start = json.loads(command("kubectl", "get", "deploy", "dispatch", "-o", "json"))
scaled = json.loads(command("kubectl", "patch", "deploy/dispatch", "--type=merge", "-p", '{"spec":{"replicas":0}}', "-o", "json"))
deadline = time.monotonic() + 90
while time.monotonic() < deadline:
    repaired = json.loads(command("kubectl", "get", "deploy", "dispatch", "-o", "json"))
    if repaired["spec"]["replicas"] == 2 and repaired.get("status", {}).get("availableReplicas", 0) == 2:
        break
    time.sleep(1)
else:
    raise SystemExit("Flux did not repair workload drift.")
Path("VERSION").write_text("dispatch-3\n")
command("python", "pipeline.py")
release = json.loads(Path("release.json").read_text())
deploy("development", release["image"])
development = commit("Validate release three in development")
wait(development)
deploy("staging", release["image"])
promotion = commit("Promote the tested digest to staging")
wait(promotion)
bad = release["image"].split("@")[0] + "@sha256:" + "0" * 64
deploy("staging", bad)
fault = commit("Rehearse an unavailable candidate image")
try:
    deadline = time.monotonic() + 120
    failure = None
    while time.monotonic() < deadline:
        pods = json.loads(command("kubectl", "get", "pods", "-l", "app=dispatch-staging", "-o", "json"))["items"]
        for pod in pods:
            for status in pod.get("status", {}).get("containerStatuses", []):
                reason = status.get("state", {}).get("waiting", {}).get("reason")
                if status["image"] == bad and reason in ("ErrImagePull", "ImagePullBackOff"):
                    failure = {"pod_uid":pod["metadata"]["uid"], "reason":reason, "image":bad}
        if failure:
            break
        time.sleep(2)
    if not failure:
        raise SystemExit("The bad candidate did not produce the expected actual image-pull failure.")
finally:
    git("revert", "--no-edit", fault)
    git("push", "origin", "main")
recovery = wait()
record = {"lab":os.environ["DOCKYARD_LAB"], "deployment_uid":start["metadata"]["uid"], "generations":[start["metadata"]["generation"], scaled["metadata"]["generation"], repaired["metadata"]["generation"]], "replicas":[start["spec"]["replicas"],scaled["spec"]["replicas"],repaired["spec"]["replicas"]], "development_commit":development, "promotion_commit":promotion, "fault_commit":fault, "recovery_commit":recovery, "failure":failure, "digest":release["digest"], "finished":time.time()}
Path("delivery-evidence.json").write_text(json.dumps(record, indent=2) + "\n")
print(json.dumps(record, indent=2))
