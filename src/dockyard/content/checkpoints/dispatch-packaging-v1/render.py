"""Resolve only documented Dockyard variables, without shell evaluation."""
import os
import re
import sys
from pathlib import Path

text = sys.stdin.read() if sys.argv[1] == '-' else Path(sys.argv[1]).read_text()

def replace(match):
    key = match.group(1)
    if key not in os.environ:
        raise SystemExit(f"Missing lab environment variable: {key}")
    return os.environ[key]

print(re.sub(r"\$\{(DOCKYARD_[A-Z_]+)\}", replace, text))
