FROM postgres:16-alpine
SHELL ["/bin/bash", "-c"]

ARG ARCHIVE_PATH="/vndb-db-latest.tar.zst"
ARG LATEST_ASSET_URL="https://dl.vndb.org/dump/vndb-db-latest.tar.zst"
ARG ASSET_DOWNLOAD_URL

RUN apk add --no-cache tar zstd curl

RUN curl -fL --retry 5 --retry-delay 5 -o "$ARCHIVE_PATH" -- "${ASSET_DOWNLOAD_URL:-$LATEST_ASSET_URL}"
RUN apk del curl

COPY initdb.sh /docker-entrypoint-initdb.d/
RUN sed -i 's/\r$//' /docker-entrypoint-initdb.d/initdb.sh

ENV ARCHIVE_PATH $ARCHIVE_PATH
ENV POSTGRES_DB vndb
ENV POSTGRES_USER vndb
ENV POSTGRES_PASSWORD vndb
ENV ON_ERROR_STOP 1

EXPOSE 5432
