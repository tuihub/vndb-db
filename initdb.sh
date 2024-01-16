#!/bin/bash

if [ -z "$ARCHIVE_PATH" ]; then
  echo "Error: missing ARCHIVE_PATH"
fi

ARCHIVE_DIR="/tmp/vndb"
IMPORT_SQL_FILE="$ARCHIVE_DIR/import.sql"
mkdir -p $ARCHIVE_DIR
tar -xvf "$ARCHIVE_PATH" -C $ARCHIVE_DIR

cd $ARCHIVE_DIR || exit
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" -f $IMPORT_SQL_FILE