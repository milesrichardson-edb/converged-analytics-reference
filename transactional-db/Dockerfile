FROM ubuntu:24.04

# Build arguments
ARG EDB_SUBSCRIPTION_TOKEN
ARG PLATFORM=linux/amd64

# Install dependencies
RUN apt-get update && apt-get install -y \
  curl \
  gnupg \
  lsb-release \
  python3 \
  python3-pip \
  python3-venv \
  && rm -rf /var/lib/apt/lists/*

# Add EDB repository
RUN curl -1sLf "https://downloads.enterprisedb.com/$EDB_SUBSCRIPTION_TOKEN/postgres_distributed/setup.deb.sh" | bash && \
  curl -1sLf "https://downloads.enterprisedb.com/$EDB_SUBSCRIPTION_TOKEN/enterprise/setup.deb.sh" | bash && \
  curl -1sLf "https://downloads.enterprisedb.com/$EDB_SUBSCRIPTION_TOKEN/dev/setup.deb.sh" | bash

# Install PGD and PGAA
RUN apt-get update && apt-get install -y \
  edb-pgd6-expanded-pgextended17 \
  edb-postgresextended-17-pgaa \
  && rm -rf /var/lib/apt/lists/*

# Install Python dependencies for config validation
RUN python3 -m pip install --break-system-packages tomli psycopg2-binary

# Create directories and set ownership
RUN mkdir -p /var/lib/postgresql/db /var/lib/postgresql/pgd-analytics && \
  chown -R postgres:postgres /var/lib/postgresql

# Copy entrypoint script
COPY docker-entrypoint.sh /usr/local/bin/
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# Set environment
ENV PGDATA=/var/lib/postgresql/db
ENV PATH=/usr/lib/edb-pge/17/bin:$PATH
ENV POSTGRES_PASSWORD=secret

# Expose ports
# 5432: Direct Postgres connection
# 6432: PGD proxy read-write
# 6433: PGD proxy read-only
EXPOSE 5432 6432 6433

# Set user
USER postgres

ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
CMD ["postgres"]
