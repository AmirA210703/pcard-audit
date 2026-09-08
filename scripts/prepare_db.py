"""Make the P-card database available to the web application.

The evidence file is ~110 MB, which is awkward to keep in git and awkward to
upload to a host.  What is committed instead is `data/pcards.db.gz` (~24 MB) --
the same 489,178 rows, VACUUMed and with indexes on Year and (Year, Month) --
and this module expands it once, on first use.

That keeps one artefact in the repository and means the deployed site has no
external dependency: no volume to mount, no file to upload by hand, nothing to
download at run time.

Resolution order for the database location:

  1. `PCARD_DB`, if it is set and the file is already there -- a local checkout
     pointing at the original download, or a host with a mounted volume.
  2. `PCARD_DB`, expanded from the .gz if the path does not exist yet.
  3. `DB_CACHE_DIR` (default: the system temp directory), expanded from the .gz.

Call it from the build step to keep start-up fast, and again at start-up so a
host with an ephemeral filesystem still comes up:

    python scripts/prepare_db.py        # build step
    ensure_db()                         # start-up, from app.py
"""
from __future__ import annotations

import gzip
import os
import shutil
import sqlite3
import sys
import tempfile

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ARCHIVE = os.path.join(REPO_ROOT, "data", "pcards.db.gz")

# The archive is only trusted if the expanded file reads back as a database with
# the expected number of rows.  A half-written file from a killed build would
# otherwise be reused for ever.
EXPECTED_ROWS = 489_178


def _usable(path: str) -> bool:
    """True if `path` is a readable P-card database with the full row count."""
    if not os.path.exists(path) or os.path.getsize(path) == 0:
        return False
    try:
        uri = "file:%s?mode=ro" % path.replace("?", "%3f").replace("#", "%23")
        with sqlite3.connect(uri, uri=True) as conn:
            rows = conn.execute("SELECT COUNT(*) FROM pcards").fetchone()[0]
    except sqlite3.Error:
        return False
    return rows == EXPECTED_ROWS


def _target() -> str:
    """Where the expanded database should live."""
    configured = (os.environ.get("PCARD_DB") or "").strip()
    if configured:
        return os.path.abspath(os.path.expanduser(configured))
    cache = os.environ.get("DB_CACHE_DIR") or tempfile.gettempdir()
    return os.path.join(cache, "pcards.db")


def _expand(target: str) -> None:
    """Expand the archive to `target` via a temporary file, then rename."""
    if not os.path.exists(ARCHIVE):
        raise FileNotFoundError(
            "Neither an expanded database nor the archive %s was found. Set PCARD_DB "
            "to your copy of pcards.db." % ARCHIVE
        )

    os.makedirs(os.path.dirname(target) or ".", exist_ok=True)

    # Write beside the target so the rename is atomic: a reader either sees no
    # file or sees the finished one, never a partial database.
    fd, staging = tempfile.mkstemp(dir=os.path.dirname(target) or ".", suffix=".partial")
    os.close(fd)
    try:
        print("expanding %s -> %s" % (os.path.relpath(ARCHIVE, REPO_ROOT), target),
              file=sys.stderr)
        with gzip.open(ARCHIVE, "rb") as src, open(staging, "wb") as dst:
            shutil.copyfileobj(src, dst, length=8 * 1024 * 1024)
        os.replace(staging, target)
    except BaseException:
        if os.path.exists(staging):
            os.unlink(staging)
        raise

    size_mb = os.path.getsize(target) / 1e6
    print("database ready: %s (%.0f MB)" % (target, size_mb), file=sys.stderr)


def ensure_db() -> str:
    """Return a path to a usable database, expanding the archive if needed.

    Also sets PCARD_DB, because `pcard_db` reads it when it is imported.
    """
    target = _target()
    if not _usable(target):
        _expand(target)
        if not _usable(target):
            raise RuntimeError(
                "Expanded %s but it does not contain the expected %d rows."
                % (target, EXPECTED_ROWS)
            )
    os.environ["PCARD_DB"] = target
    return target


if __name__ == "__main__":
    print(ensure_db())
