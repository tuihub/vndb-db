# VNDB Databases

Query [VNDB database dumps](https://vndb.org/d14) with PostgreSQL or SQLite.  
通过 PostgreSQL 或 SQLite 查询 [VNDB 数据库转储](https://vndb.org/d14)中的数据。  

Both builds use the table definitions included in the VNDB dump.  
两种构建方式都使用 VNDB 转储附带的表定义。  

## PostgreSQL

*Changes to the dump format may break the import script.*  
*转储格式变化可能导致导入脚本失效。*  

Requires 3 GB of disk space.  
The build may take a long time.  
构建需要 3 GB 磁盘空间。  
构建可能耗时较长。  

### Usage

```bash
cd postgresql
# Build and start
docker compose up -d
# Stop
docker compose down
# Force rebuild
docker compose up --build --force-recreate --no-deps -d
# 自定义转储下载地址
ASSET_DOWNLOAD_URL="https://[YOUR_DOWNLOAD_URL]" docker compose up --build -d
```

## SQLite

*Changes to the dump format may break the import script.*  
*转储格式变化可能导致导入脚本失效。*  

Requires disk space for the dump and the new database.  
The build may take a long time.  
构建需要为转储和新数据库预留磁盘空间。  
构建可能耗时较长。  

### Usage

Prebuilt SQLite databases contain public catalog data and are available on the [release page](https://github.com/tuihub/vndb-db/releases/tag/sqlite). Each ZIP uses the source dump's date, contains `vndb.sqlite`, and comes with a `.sha256` checksum file. The `dump_info` table contains the dump timestamp and license texts.  
预构建的 SQLite 数据库包含公开的作品目录数据，可在 [发布页](https://github.com/tuihub/vndb-db/releases/tag/sqlite) 下载。ZIP 沿用对应转储的日期，内含 `vndb.sqlite`，并附有 `.sha256` 校验文件。`dump_info` 表记录转储时间和许可文本。  

```bash
# Replace with a filename from the release page
archive="vndb-db-YYYY-MM-DD.zip"
curl -fLO "https://github.com/tuihub/vndb-db/releases/download/sqlite/$archive"
unzip "$archive"
# Look up a title by its VNDB ID
sqlite3 -readonly vndb.sqlite "SELECT title FROM vn_titles WHERE id = 'v4';"
```

The `game_titles` index supports substring searches of at least three characters across titles and their romanizations.  
可用 `game_titles` 索引搜索标题及其罗马字转写，搜索片段至少包含三个字符。  

### Build

Local builds import the full dump by default. With `--catalog-only`, the Python build imports only the public catalog tables.  
本地构建默认导入完整转储。Python 构建命令加上 `--catalog-only` 后，只导入公开作品目录所需的表。  

```bash
cd sqlite
# Build
docker compose run --build --rm sqlite
# 自定义转储下载地址
ASSET_DOWNLOAD_URL="https://[YOUR_DOWNLOAD_URL]" docker compose run --build --rm sqlite
```

Use Python 3 to build the database directly from a downloaded dump. The build requires `zstd` on `PATH`. Python's `sqlite3` module must use SQLite 3.34 or later with FTS5 enabled. Check the environment by running `python3 build.py --check` from `sqlite/`.  
用 Python 3 直接从下载的转储文件建库。构建时需能从 `PATH` 找到 `zstd`。`sqlite3` 模块所用的 SQLite 需为 3.34 或更高版本，且已启用 FTS5。在 `sqlite/` 下运行 `python3 build.py --check` 可检查环境。  

```bash
cd sqlite
mkdir -p data
python3 build.py /path/to/vndb-db-latest.tar.zst data/vndb.sqlite
```
