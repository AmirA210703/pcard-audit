#!/bin/sh
# Convenience launcher for local use. Set ANTHROPIC_API_KEY in your shell (or a .env
# you never commit) before running; it is deliberately not stored in this file.
set -e
: "${PCARD_DB:=$(cd "$(dirname "$0")/.." && pwd)/pcards.db}"
export PCARD_DB
echo "database : $PCARD_DB"
if [ -z "$ANTHROPIC_API_KEY" ]; then
  echo "warning  : ANTHROPIC_API_KEY is not set - the 'Ask the data' tab will be disabled."
fi
exec python app.py
