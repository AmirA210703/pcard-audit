"""Load a local .env file into os.environ.

Kept dependency-free on purpose: the file is read here rather than through
python-dotenv so that the app works straight after `pip install -r
requirements.txt` without an extra package, and so there is one obvious place
to look when a key is not being picked up.

Rules:
  * a real environment variable always wins over the file, so
    `ANTHROPIC_API_KEY=... python app.py` overrides .env for one run
  * blank lines and `#` comments are ignored
  * `export KEY=value` is accepted, as are single or double quotes around the value
  * the file is never written to and never logged
"""
from __future__ import annotations

import os

DEFAULT_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")


def load(path: str | None = None, override: bool = False) -> list[str]:
    """Read `path` into os.environ. Returns the names of the keys that were set."""
    path = path or os.environ.get("ENV_FILE") or DEFAULT_PATH
    if not os.path.exists(path):
        return []

    loaded = []
    with open(path, encoding="utf-8") as fh:
        for raw in fh:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if line.startswith("export "):
                line = line[len("export "):].lstrip()
            if "=" not in line:
                continue

            key, value = line.split("=", 1)
            key = key.strip()
            value = value.strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
                value = value[1:-1]

            if not key:
                continue
            if key in os.environ and not override:
                continue          # a real environment variable wins
            os.environ[key] = value
            loaded.append(key)

    return loaded
