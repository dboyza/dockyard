from pathlib import Path
import yaml

p = Path("release/overlays/production/kustomization.yaml")
d = yaml.safe_load(p.read_text())
d["configMapGenerator"] = [
    {
        "name": "release-metadata",
        "behavior": "merge",
        "literals": ["environment=production", "release=dispatch-approved-b"],
    }
]
p.write_text(yaml.safe_dump(d))
