"""Small explicit helpers; Git and Flux remain the actual delivery systems."""
import json
import os
import subprocess
import sys
import time
from pathlib import Path
import yaml

ROOT = Path("delivery")
def command(*args):
    result = subprocess.run(list(args), check=True, capture_output=True, text=True)
    return result.stdout.strip()
def git(*args):
    return command("git", "-C", str(ROOT), *args)
def commit(message):
    git("add", "environments")
    if git("status", "--porcelain"):
        git("commit", "-m", message)
    git("push", "origin", "main")
    return git("rev-parse", "HEAD")
def deploy(environment, image):
    path = ROOT / "environments" / environment
    path.mkdir(parents=True, exist_ok=True)
    document = yaml.safe_load(Path("deployment-template.yaml").read_text())
    if environment == "staging":
        document["metadata"]["name"] = "dispatch-staging"
        document["spec"]["replicas"] = 1
        document["spec"]["selector"]["matchLabels"] = {"app":"dispatch-staging"}
        document["spec"]["template"]["metadata"]["labels"] = {"app":"dispatch-staging"}
    document["spec"]["template"]["spec"]["containers"][0]["image"] = image
    (path / "deployment.yaml").write_text(yaml.safe_dump(document, sort_keys=False))
    (path / "kustomization.yaml").write_text("apiVersion: kustomize.config.k8s.io/v1beta1\nkind: Kustomization\nresources: [deployment.yaml]\n")
def wait(revision=None):
    revision = revision or git("rev-parse", "HEAD")
    deadline = time.monotonic() + 180
    while time.monotonic() < deadline:
        ready = True
        for environment in ("development", "staging"):
            item = json.loads(command("kubectl", "get", "kustomization.kustomize.toolkit.fluxcd.io", environment, "-n", "flux-system", "-o", "json"))
            status = item.get("status", {})
            ready &= status.get("lastAppliedRevision", "").endswith(":" + revision) and any(c["type"] == "Ready" and c["status"] == "True" and c.get("observedGeneration") == item["metadata"]["generation"] for c in status.get("conditions", []))
        if ready:
            return revision
        time.sleep(2)
    raise SystemExit("Flux did not apply the current commit within three minutes; inspect its conditions.")

if __name__ == "__main__":
    if sys.argv[1] == "seed":
        ROOT.mkdir(exist_ok=True)
        if not (ROOT / ".git").is_dir():
            command("git", "init", "--initial-branch=main", str(ROOT))
            git("config", "user.name", "Dockyard learner")
            git("config", "user.email", "learner@dockyard.local")
            git("config", "commit.gpgsign", "false")
            git("remote", "add", "origin", os.environ["DOCKYARD_GIT_URL"])
        release = json.loads(Path("release.json").read_text())
        for environment in ("development", "staging"):
            deploy(environment, release["image"])
        print(commit("Declare tested Dispatch release"))
    elif sys.argv[1] == "wait":
        print(wait())
    else:
        raise SystemExit("Use seed or wait.")
