# VNDB Dump Docker Container

This repository provides a way to access the [VNDB Database Dumps](https://vndb.org/d14) through postgresql.  
本仓库提供了通过 postgresql 访问[VNDB Database Dumps](https://vndb.org/d14)的方法。

*The script may break due to the future changes of the dump.*  
*脚本可能会由于未来dump文件的变化而失效。*  

Requires 3GB of disk space.  
Build process may take a long time.  
需要3GB的磁盘空间。  
构建过程可能需要较长时间。  

## Usage

```bash
# Build and start
docker compose up -d
# Stop
docker compose down
# Force rebuild
docker-compose up --build --force-recreate --no-deps -d
# 如果你网络不佳，可以自定义dump文件的下载地址
ASSET_DOWNLOAD_URL="https://[YOUR_DOWNLOAD_URL]" docker compose up -d
```

## SQLite

Download the current [upstream archive](https://vndb.org/d14). Build a standalone SQLite database with Python 3. The converter streams the archive and replaces the output only after a successful import.

下载[上游转储](https://vndb.org/d14)，使用 Python 3 生成可独立查询的 SQLite 文件。转换器逐表读入数据，导入成功后才替换现有文件。

```sh
python3 sqlite/build.py vndb-db-latest.tar.zst vndb.sqlite
sqlite3 -readonly vndb.sqlite "SELECT title FROM vn_titles WHERE id = 'v4';"
```

The converter reads the plain schema and PostgreSQL COPY records, preserving keys, NULLs, escaped text and table names. Boolean values become 0/1, integer types have SQLite integer affinity, and arrays retain their PostgreSQL text representation. The dump_info table contains the upstream timestamp, attribution and license texts. Install zstd on PATH.

需要安装 zstd。保留原表名、主键、空值和转义文本，布尔值存为 0/1。dump_info 表附有数据时间、来源说明及各项数据许可。

A maintainer can run **Publish SQLite catalog** in GitHub Actions. The `sqlite` release contains `vndb.sqlite.gz` and its SHA-256 checksum. Verify the compressed file, then decompress it before opening the database.

维护者可手动运行 **Publish SQLite catalog**，从 `sqlite` 发布页下载压缩数据库和 SHA-256 校验文件。校验后解压即可查询。

Published builds use `--catalog-only` to select catalog tables without distributing personal lists or user votes. Local conversion defaults to the complete upstream dump. Source-specific licensing and the upstream timestamp are available in `dump_info`.

公开发行文件只选取作品目录相关表。本机转换默认导入完整转储，许可及来源时间保存在 `dump_info`。

The `game_titles` FTS5 trigram index accepts quoted substring searches of at least three Unicode characters and returns the original `id`. Shorter searches can query the source title columns. Building requires SQLite 3.34 or newer with FTS5.

可通过 `game_titles` 的 FTS5 三元组索引，以三个以上字符的片段检索原始条目 ID。构建环境需要支持 FTS5 的 SQLite 3.34 或更新版本。
