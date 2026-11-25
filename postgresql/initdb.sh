#!/bin/bash
set -euo pipefail

if [ -z "$ARCHIVE_PATH" ]; then
  echo "ARCHIVE_PATH is empty. Set it to the dump archive path."
  exit 1
fi

ARCHIVE_DIR="/tmp/vndb"
IMPORT_SQL_FILE="$ARCHIVE_DIR/import.sql"
IMPORT_SQL_WITHOUT_FOREIGN_KEYS="$ARCHIVE_DIR/import-without-foreign-keys.sql"
mkdir -p $ARCHIVE_DIR
tar -xvf "$ARCHIVE_PATH" -C $ARCHIVE_DIR

cd $ARCHIVE_DIR || exit
# Skip foreign-key creation because the dump can contain dangling references.
sed '/ ADD CONSTRAINT .* FOREIGN KEY /d' "$IMPORT_SQL_FILE" > "$IMPORT_SQL_WITHOUT_FOREIGN_KEYS"
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" -f "$IMPORT_SQL_WITHOUT_FOREIGN_KEYS"
