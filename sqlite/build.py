"""Build a standalone SQLite database from a VNDB .tar.zst dump."""
import argparse
import os
import re
import shutil
import subprocess
import tarfile
import tempfile
from contextlib import closing
from pathlib import Path

try:
    import sqlite3
except ImportError as error:
    raise SystemExit(f"The sqlite3 module is unavailable ({error}).") from None

CREATE_GAME_TITLES_TABLE = (
    "CREATE VIRTUAL TABLE game_titles "
    "USING fts5(id UNINDEXED, title, tokenize='trigram')"
)

ESCAPES = {b"b": b"\b", b"f": b"\f", b"n": b"\n", b"r": b"\r", b"t": b"\t", b"v": b"\v"}
ESCAPE = re.compile(rb"\\([0-7]{1,3}|x[0-9a-fA-F]{1,2}|.)")
INTEGER = {"integer", "smallint", "bigint", "animation", "boolean"}

CATALOG = {
    "vn", "vn_titles", "vn_editions", "vn_extlinks", "vn_relations", "vn_screenshots",
    "vn_staff", "staff", "staff_alias", "releases", "releases_vn", "releases_titles",
    "releases_producers", "releases_extlinks", "releases_platforms", "producers", "extlinks", "images",
}


def check_environment():
    if shutil.which("zstd") is None:
        raise SystemExit("Install zstd and make it available on PATH to read VNDB dumps.")
    try:
        with closing(sqlite3.connect(":memory:")) as db:
            db.execute(CREATE_GAME_TITLES_TABLE)
    except sqlite3.Error as error:
        raise SystemExit(
            f"SQLite {sqlite3.sqlite_version} cannot create an FTS5 trigram index ({error}). "
            "Use Python with SQLite 3.34 or later and FTS5 enabled."
        ) from None


def unescape(match):
    code = match[1]
    if code[:1] in b"01234567":
        return bytes([int(code, 8)])
    if code.startswith(b"x") and len(code) > 1:
        return bytes([int(code[1:], 16)])
    return ESCAPES.get(code, code)


def value(field, pgtype):
    if field == rb"\N":
        return None
    if pgtype == "boolean":
        return {b"t": 1, b"f": 0}[field]
    return (ESCAPE.sub(unescape, field) if b"\\" in field else field).decode()


def ident(name):
    return '"' + name.replace('"', '""') + '"'


def schema(db, text, catalog_only):
    tables = {}
    for name, body in re.findall(r"CREATE TABLE (\w+) \(\n(.*?)\n\);", text, re.S):
        if catalog_only and name not in CATALOG:
            continue
        fields = {}
        definitions = []
        for line in body.splitlines():
            line = line.strip().rstrip(",")
            if line.startswith("PRIMARY KEY("):
                keys = [ident(key.strip()) for key in line[12:-1].split(",")]
                definitions.append("PRIMARY KEY (" + ",".join(keys) + ")")
            else:
                column, pgtype, *_ = line.split()
                fields[column] = pgtype
                affinity = "INTEGER" if pgtype in INTEGER else "TEXT"
                definitions.append(ident(column) + " " + affinity + (" NOT NULL" if "NOT NULL" in line else ""))
        db.execute(f"CREATE TABLE {ident(name)} ({','.join(definitions)})")
        tables[name] = fields
    if "vn_titles" not in tables:
        raise ValueError("Missing VNDB schema")
    return tables


def load(db, source, catalog_only):
    tables = {}
    loaded = set()
    headers = {}
    db.execute("CREATE TABLE dump_info (name TEXT PRIMARY KEY, content TEXT NOT NULL)")
    for member in source:
        if not member.isfile():
            continue
        name = member.name
        stream = source.extractfile(member)
        if name == "schema_plain.sql":
            tables = schema(db, stream.read().decode(), catalog_only)
        elif name.startswith("LICENSE-") or name in {"TIMESTAMP", "README.txt"}:
            db.execute("INSERT INTO dump_info VALUES (?,?)", (name, stream.read().decode()))
        elif name.startswith("db/"):
            table = name[3:]
            if catalog_only and table.removesuffix(".header") not in tables:
                continue
            if table.endswith(".header"):
                headers[table[:-7]] = stream.read().decode().split()
                continue
            print(table, flush=True)
            fields = tables[table]
            sql = f"INSERT INTO {ident(table)} VALUES ({','.join('?' for key in fields)})"
            def rows():
                for line in stream:
                    cells = line.rstrip(b"\n").split(b"\t")
                    if len(cells) != len(fields):
                        raise ValueError(f"Unexpected row width in {table}")
                    yield tuple(value(cell, kind) for cell, kind in zip(cells, fields.values()))
            db.executemany(sql, rows())
            loaded.add(table)
    if loaded != set(tables) or headers != {key: list(fields) for key, fields in tables.items()}:
        raise ValueError("COPY headers or table inventory differ from schema_plain.sql")


def convert(archive, output, catalog_only=False):
    check_environment()
    with tempfile.TemporaryDirectory(dir=output.parent) as temp:
        stage = Path(temp) / "vndb.sqlite"
        with closing(sqlite3.connect(stage)) as db, db:
            db.execute("BEGIN")
            with subprocess.Popen(["zstd", "-dc", "--", archive], stdout=subprocess.PIPE) as decoder:
                with decoder.stdout, tarfile.open(fileobj=decoder.stdout, mode="r|") as source:
                    load(db, source, catalog_only)
                    db.execute("CREATE INDEX releases_vn_vid ON releases_vn(vid)")
                    db.execute(CREATE_GAME_TITLES_TABLE)
                    db.execute("INSERT INTO game_titles SELECT id,title FROM vn_titles UNION ALL SELECT id,latin FROM vn_titles WHERE latin IS NOT NULL")
                if decoder.wait():
                    raise ValueError("Invalid zstd archive")
        os.replace(stage, output)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="check for zstd and FTS5 trigram support and exit")
    parser.add_argument("--catalog-only", action="store_true", help="include only the public catalog tables")
    parser.add_argument("archive", type=Path, nargs="?")
    parser.add_argument("output", type=Path, nargs="?")
    args = parser.parse_args()
    if args.check:
        check_environment()
        print(f"zstd is available. SQLite {sqlite3.sqlite_version} supports FTS5 trigram indexes.")
    elif args.archive is None or args.output is None:
        parser.error("archive and output are required")
    else:
        convert(args.archive, args.output, args.catalog_only)
