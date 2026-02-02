# Transactional Database: PGD + PGAA

This component provides the transactional database using Postgres with PGD (Postgres Distributed) and PGAA extensions.

## Components

- **PGD**: Postgres with BDR (Bi-Directional Replication) extension for multi-master replication
- **PGAA**: Postgres Analytics Accelerator for replicating data to Iceberg tables

## Prerequisites

- EDB Subscription Token (set in `.env` file)
- Catalog component must be running (Lakekeeper + MinIO)

## Configuration

Set your EDB subscription token in `.env`:

```bash
EDB_SUBSCRIPTION_TOKEN=your_token_here
```

The database configuration is defined in `/demo-config.toml`:

```toml
[catalog]
name = "demo_catalog"
url = "http://lakekeeper:8181"

[database.transactional]
node_group = "pgd-group"
host = "pgd"
port = 5432
database = "demo"
user = "postgres"
password = "secret"
```

## Quick Start

```bash
# Build and start
docker-compose up -d --build

# Check logs
docker-compose logs -f pgd

# Connect to database
psql -h localhost -p 7432 -U postgres -d demo

# Stop
docker-compose down
```

## Connection Details

- **Host**: localhost
- **Port**: 7432 (direct connection)
- **Database**: demo
- **User**: postgres
- **Password**: secret

### PGD Proxy Ports

- **6432**: Read-write connection (PGD proxy)
- **6433**: Read-only connection (PGD proxy)

## Database Setup

The entrypoint script automatically:

1. Initializes PostgreSQL database
2. Creates `demo` database
3. Installs `bdr` and `pgaa` extensions
4. Creates PGD node group (`pgd-group`)
5. Configures local filesystem storage location
6. Configures Iceberg REST Catalog (from `demo-config.toml`)
7. Tests catalog connection
8. Sets default analytics write catalog
9. Validates configuration matches `demo-config.toml`

## Creating Tables with Analytics Replication

```sql
-- Create a table that replicates to Iceberg
CREATE TABLE demo.sales (
    id SERIAL,
    country VARCHAR(100),
    product VARCHAR(100),
    quantity INT,
    revenue DECIMAL(10,2),
    sale_date DATE,
    PRIMARY KEY (id, sale_date)
) WITH (pgd.replicate_to_analytics = true);

-- Insert data (automatically replicated to Iceberg)
INSERT INTO demo.sales (country, product, quantity, revenue, sale_date)
VALUES ('USA', 'Widget', 10, 100.00, '2024-01-01');

-- Wait for replication to complete
SELECT bdr.wait_slot_confirm_lsn(NULL, NULL);

-- Read from analytics engine (Iceberg)
SET bdr.prefer_analytics_engine = true;
SELECT * FROM demo.sales;

-- Read from transactional engine (Postgres)
SET bdr.prefer_analytics_engine = false;
SELECT * FROM demo.sales;
```

## Volumes

- `pgd-data`: PostgreSQL database files
- `pgd-analytics`: Local filesystem location for Iceberg files (fallback)

## Troubleshooting

```bash
# Check if extensions are loaded
docker-compose exec pgd psql -U postgres -d demo -c '\dx'

# Check PGD node group
docker-compose exec pgd psql -U postgres -d demo -c 'SELECT * FROM bdr.node_group;'

# Check catalog configuration
docker-compose exec pgd psql -U postgres -d demo -c 'SELECT * FROM pgaa.list_catalogs();'

# Check analytics write catalog
docker-compose exec pgd psql -U postgres -d demo -c "
  SELECT * FROM bdr.node_group_option
  WHERE node_group_name = 'pgd-group'
  AND option_name = 'analytics_write_catalog';
"

# Restart container
docker-compose restart pgd
```

## Configuration Validation

The entrypoint script validates that the configured analytics write catalog matches `demo-config.toml`. If there's a mismatch, the container will exit with an error. To fix:

1. Update `demo-config.toml` to match the running configuration, OR
2. Remove volumes and rebuild:
   ```bash
   docker-compose down -v
   docker-compose up -d --build
   ```
