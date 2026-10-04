"""Sign this release with the token read from standard input."""

import hashlib
import hmac
import sys
from pathlib import Path

token = sys.stdin.read().strip()
if not token:
    raise SystemExit("No release token arrived on standard input, so the release cannot be signed.")
print(hmac.new(token.encode(), Path("VERSION").read_bytes(), hashlib.sha256).hexdigest())
