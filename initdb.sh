#!/bin/bash
set -euo pipefail

if [ -z "$ARCHIVE_PATH" ]; then
  echo "Error: missing ARCHIVE_PATH"
  exit 1
fi

ARCHIVE_DIR="/tmp/vndb"
IMPORT_SQL_FILE="$ARCHIVE_DIR/import.sql"
IMPORT_SQL_WITHOUT_FOREIGN_KEYS="$ARCHIVE_DIR/import-without-foreign-keys.sql"
mkdir -p $ARCHIVE_DIR
tar -xvf "$ARCHIVE_PATH" -C $ARCHIVE_DIR

cd $ARCHIVE_DIR || exit
# The upstream dump can contain rows that violate late-added foreign-key checks,
# while downstream users of this image often only need the imported data tables.
# Keep the data import strict, but skip foreign-key constraint creation so a
# dangling reference does not make the whole database container unusable.
sed '/ ADD CONSTRAINT .* FOREIGN KEY /d' "$IMPORT_SQL_FILE" > "$IMPORT_SQL_WITHOUT_FOREIGN_KEYS"
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" -f "$IMPORT_SQL_WITHOUT_FOREIGN_KEYS"
