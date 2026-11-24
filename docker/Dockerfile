FROM postgis/postgis:18-3.7

RUN apt-get update \
    && apt-get install -y --no-install-recommends postgresql-18-h3 \
    && rm -rf /var/lib/apt/lists/*

COPY 20-extensions.sql /docker-entrypoint-initdb.d/
