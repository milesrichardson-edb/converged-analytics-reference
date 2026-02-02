#!/bin/bash
set -euo pipefail

# Configuration file path (mounted from host)
CONFIG_FILE="${CONFIG_FILE:-/config/demo-config.toml}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $*"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $*"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $*"
}

# Parse TOML configuration using Python
parse_config() {
    local key="$1"
    python3 -c "
import tomli
import sys

try:
    with open('$CONFIG_FILE', 'rb') as f:
        config = tomli.load(f)

    # Navigate nested keys (e.g., 'catalog.name')
    keys = '$key'.split('.')
    value = config
    for k in keys:
        value = value[k]

    print(value)
except Exception as e:
    sys.stderr.write(f'Error parsing config: {e}\n')
    sys.exit(1)
"
}

# Validate configuration file exists
if [ ! -f "$CONFIG_FILE" ]; then
    log_error "Configuration file not found: $CONFIG_FILE"
    log_error "Please ensure demo-config.toml is mounted at /config/demo-config.toml"
    exit 1
fi

log_info "Using configuration file: $CONFIG_FILE"

# Parse catalog configuration
CATALOG_NAME=$(parse_config "catalog.name")
CATALOG_TYPE=$(parse_config "catalog.type")
CATALOG_URL=$(parse_config "catalog.url")
CATALOG_WAREHOUSE=$(parse_config "catalog.warehouse")
CATALOG_WAREHOUSE_NAME=$(parse_config "catalog.warehouse_name")

# Parse object store configuration (needed for warehouse creation)
MINIO_ENDPOINT=$(parse_config "object_store.endpoint")
MINIO_BUCKET=$(parse_config "object_store.bucket")
MINIO_ACCESS_KEY=$(parse_config "object_store.access_key")
MINIO_SECRET_KEY=$(parse_config "object_store.secret_key")

log_info "Catalog configuration:"
log_info "  Name: $CATALOG_NAME"
log_info "  Type: $CATALOG_TYPE"
log_info "  URL: $CATALOG_URL"
log_info "  Warehouse: $CATALOG_WAREHOUSE"
log_info "  Warehouse Name: $CATALOG_WAREHOUSE_NAME"

# Set default password if not provided
PGPASSWORD=${POSTGRES_PASSWORD:-secret}
export PGPASSWORD

# Check if database is already initialized
if [ ! -f "/var/lib/postgresql/db/PG_VERSION" ]; then
    log_info "Initializing PGD cluster..."

    # Initialize PGD cluster using pgd node setup
    /usr/lib/edb-pge/17/bin/pgd node db1 setup \
        --dsn "host=0.0.0.0 dbname=demo user=postgres password=${POSTGRES_PASSWORD}" \
        --pgdata /var/lib/postgresql/db \
        --log-file /var/lib/postgresql/logfile \
        --group-name pgd-group

    # Configure PGAA settings in postgresql.conf
    cat >> /var/lib/postgresql/db/postgresql.conf <<EOF

# PGAA Configuration
pgfs.allowed_local_fs_paths = '/var/lib/postgresql/pgd-analytics'
pgaa.autostart_seafowl_port = 5445
pgaa.seafowl_url = 'http://localhost:5445'
listen_addresses = '*'

# Faster sync of catalog changes (e.g. new tables) within 30 seconds (not default 60)
pgaa.metastore_sync_poll_rate_s=30
pgaa.metastore_sync_stale_duration_s=30

# Faster tiered tables creation (1 second wakeup instead of 5 minutes)
bdr.taskmgr_nap_time=1000

# Collect statistics for all tables
edb.collect_table_statistics=all

# Faster replication (reduce from default 30)
pgaa.max_replication_lag_s=5
pgaa.flush_task_interval_s=5

EOF

    # Update pg_hba.conf to allow connections from all hosts
    echo "host    all             all             0.0.0.0/0               md5" >> /var/lib/postgresql/db/pg_hba.conf

    log_info "PGD cluster initialized successfully"
else
    log_info "Database already initialized, starting PostgreSQL..."
    # Start PostgreSQL manually since pgd node setup was already run
    /usr/lib/edb-pge/17/bin/pg_ctl -D /var/lib/postgresql/db -l /var/lib/postgresql/logfile start
fi

# Wait for PostgreSQL to be ready
log_info "Waiting for PostgreSQL to be ready..."
for i in {1..30}; do
    if /usr/lib/edb-pge/17/bin/pg_isready -h localhost -U postgres -d demo > /dev/null 2>&1; then
        log_info "PostgreSQL is ready"
        break
    fi
    if [ $i -eq 30 ]; then
        log_error "PostgreSQL failed to be ready within 30 seconds"
        exit 1
    fi
    sleep 1
done

# Create PGAA extension if not exists
log_info "Creating PGAA extension..."
PGPASSWORD=$POSTGRES_PASSWORD /usr/lib/edb-pge/17/bin/psql -h localhost -U postgres -d demo -c "CREATE EXTENSION IF NOT EXISTS pgaa CASCADE;" || true

# Look up warehouse ID from Lakekeeper (warehouse should be created by catalog stack)
# Extract base URL (remove /catalog suffix for management API calls)
BASE_URL=$(echo "$CATALOG_URL" | sed 's|/catalog$||')
log_info "Looking up warehouse '$CATALOG_WAREHOUSE_NAME' in Lakekeeper..."
WAREHOUSE_LIST=$(curl -s "${BASE_URL}/management/v1/warehouse" 2>&1 || echo '{"warehouses":[]}')
WAREHOUSE_ID=$(echo "$WAREHOUSE_LIST" | python3 -c "import sys, json; data=json.load(sys.stdin); warehouses=[w for w in data.get('warehouses', []) if w.get('name') == '$CATALOG_WAREHOUSE_NAME']; print(warehouses[0]['id'] if warehouses else '')" 2>/dev/null || echo "")

if [ -z "$WAREHOUSE_ID" ]; then
    log_info "ERROR: Warehouse '$CATALOG_WAREHOUSE_NAME' not found in Lakekeeper. Please ensure catalog stack is running."
    exit 1
fi

log_info "Using warehouse ID: $WAREHOUSE_ID"

# Configure catalog if not already done (no need to create namespace - catalog will handle it)
log_info "Configuring PGAA catalog..."
CATALOG_EXISTS=$(PGPASSWORD=$POSTGRES_PASSWORD /usr/lib/edb-pge/17/bin/psql -h localhost -U postgres -d demo -tAc \
    "SELECT COUNT(*) FROM pgaa.list_catalogs() WHERE name = '$CATALOG_NAME';" 2>/dev/null || echo "0")

if [ "$CATALOG_EXISTS" = "0" ]; then
    log_info "Creating catalog: $CATALOG_NAME"

    # Add the catalog with proper parameters
    PGPASSWORD=$POSTGRES_PASSWORD /usr/lib/edb-pge/17/bin/psql -h localhost -U postgres -d demo <<EOSQL
SELECT bdr.replicate_ddl_command(\$\$
  SELECT pgaa.add_catalog(
    '$CATALOG_NAME',
    '$CATALOG_TYPE',
    '{
      "url": "$CATALOG_URL",
      "warehouse": "$WAREHOUSE_ID",
      "warehouse_name": "$CATALOG_WAREHOUSE_NAME"
    }'
  );
\$\$);
EOSQL

    # Set as default write catalog
    log_info "Setting $CATALOG_NAME as default write catalog..."
    PGPASSWORD=$POSTGRES_PASSWORD /usr/lib/edb-pge/17/bin/psql -h localhost -U postgres -d demo <<EOSQL
SELECT bdr.alter_node_group_option('pgd-group', 'analytics_write_catalog', '$CATALOG_NAME');
EOSQL

    log_info "Catalog configuration complete!"
else
    log_info "Catalog $CATALOG_NAME already exists"
fi

# PostgreSQL is already running from pgd node setup, just keep it running
log_info "Configuration complete! PostgreSQL is running."
log_info "Use 'docker logs -f pgd' to monitor the server."

# Keep container running by tailing PostgreSQL log
exec tail -f /var/lib/postgresql/logfile
