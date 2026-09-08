#!/bin/sh
# Run one audit query against the P-card database.
#   ./run.sh sql/qry_T2_Question4.sql          formatted for reading
#   ./run.sh sql/qry_T3_Question2.sql csv      as CSV
set -e
[ -n "$1" ] || { echo "usage: $0 <query.sql> [column|csv|list]" >&2; exit 1; }
DB="${PCARD_DB:-$(cd "$(dirname "$0")" && pwd)/pcards.db}"
[ -f "$DB" ] || { echo "database not found: $DB (set PCARD_DB)" >&2; exit 1; }
exec sqlite3 -header "-${2:-column}" "$DB" < "$1"
