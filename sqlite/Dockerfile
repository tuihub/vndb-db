FROM python:3.12-slim-bookworm

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl zstd \
    && rm -rf /var/lib/apt/lists/*

COPY build.py initdb.sh /app/
RUN sed -i 's/\r$//' /app/initdb.sh

ENTRYPOINT ["sh", "/app/initdb.sh"]
