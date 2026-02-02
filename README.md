# Converged Analytics Demo

A complete demonstration of converged analytics using EnterpriseDB (EDB) technologies: Postgres with PGD (Postgres Distributed), WarehousePG, PGAA (Postgres Analytics Accelerator), Apache Iceberg, Lakekeeper, and Apache Spark with optional RAPIDS GPU acceleration.

> [!IMPORTANT]
> **Support Disclaimer**: This repository and the code artifacts contained herein are provided for educational and tutorial purposes only. This project is **not supported by EnterpriseDB (EDB)**. Use of this code is at your own risk and is not covered by any EDB support agreements or SLAs.

## Status of this Repo

You can run PGD (transactional), WHPG (analytical) and Catalog services.
Spark part is WIP.

(Disclaimer: Created with assistance of VSCode Co-Pilot and Claude Sonnet 4.5)

## Overview

This demo showcases how to build a modern data platform that converges OLTP and OLAP workloads:

1. **Transactional Database (PGD + PGAA)**: Postgres with multi-master replication and automatic replication to Iceberg tables
2. **Catalog & Object Store (Lakekeeper + MinIO)**: Iceberg REST Catalog and S3-compatible storage for analytics data
3. **Compute Engine (Spark Connect)**: Distributed query processing with optional GPU acceleration via RAPIDS
4. **Analytics Database (WarehousePG + PGAA)**: Postgres-based data warehouse for analytics queries on Iceberg data

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    Converged Analytics Stack                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐         ┌──────────────┐                    │
│  │     PGD      │────────▶│  Lakekeeper  │                    │
│  │   (OLTP)     │         │  + MinIO     │                    │
│  │   + PGAA     │         │  (Catalog)   │                    │
│  └──────────────┘         └──────────────┘                    │
│         │                        │                              │
│         │                        │                              │
│         │                        ▼                              │
│         │              ┌──────────────┐                        │
│         │              │    Spark     │                        │
│         │              │   Connect    │                        │
│         │              │  (RAPIDS)    │                        │
│         │              └──────────────┘                        │
│         │                        │                              │
│         │                        │                              │
│         ▼                        ▼                              │
│  ┌──────────────────────────────────┐                         │
│  │       WarehousePG + PGAA         │                         │
│  │      (Analytics Queries)         │                         │
│  │   • Datafusion (Seafowl)         │                         │
│  │   • Spark Connect                │                         │
│  └──────────────────────────────────┘                         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Prerequisites

### Required

- **Docker** (>= 20.10)
- **docker-compose** (>= 1.29)
- **Python** (>= 3.10)
- **uv** (Python package manager) - Install with:
  ```bash
  curl -LsSf https://astral.sh/uv/install.sh | sh
  ```
- **EDB Subscription Token** - Create an account at [enterprisedb.com/accounts](https://www.enterprisedb.com/accounts/) which starts with a 60 day trial. Get your token from Account → Repos → Subscription Token.

### Optional

- **NVIDIA GPU + CUDA** (for RAPIDS acceleration)
- **NVIDIA Container Toolkit** (for Docker GPU support)

## Quick Start

### 1. Clone and Configure

```bash
# Set your EDB subscription token
echo "EDB_SUBSCRIPTION_TOKEN=your_token_here" > transactional-db/.env
echo "EDB_SUBSCRIPTION_TOKEN=your_token_here" > analytics-db/.env

# Remote Docker context: Copy config to remote host
# If using a remote Docker context (e.g., EC2), copy the config file to the remote host:
scp demo-config.toml $REMOTE_DOCKER_HOST:/home/ec2-user/converged-analytics-reference/
# Note: docker-compose.yml files are configured for remote context. For local Docker, edit volume mounts.

# Review and customize configuration (optional)
cat demo-config.toml
```

### 2. Install Python Dependencies

```bash
cd scripts
uv venv
source .venv/bin/activate  # On macOS/Linux
uv pip install -e .
```

### 3. Start the Stack

```bash
# Start all components in order
./scripts/start-demo.sh start

# This will:
# 1. Start MinIO and Lakekeeper (catalog)
# 2. Start PGD with PGAA (transactional database)
# 3. Start Spark Connect cluster
# 4. Start WarehousePG with PGAA (analytics database)
```

### 4. Generate Demo Data

```bash
# Create tables and load synthetic data
python3 scripts/generate_data.py --all

# Or append more data to existing tables (can run multiple times)
python3 scripts/generate_data.py --append

# Or generate larger datasets with scale factor (e.g., 10x the configured data)
python3 scripts/generate_data.py --append --scale-factor 10
```

### 5. Run Example Queries

```bash
# Run all query examples
python3 scripts/query_examples.py --all

# Or run specific examples:
python3 scripts/query_examples.py --pgd-transactional
python3 scripts/query_examples.py --pgd-analytics
python3 scripts/query_examples.py --whpg-datafusion
python3 scripts/query_examples.py --whpg-spark
```

## Components

### [Catalog](catalog/)

Iceberg REST Catalog (Lakekeeper) and S3-compatible object storage (MinIO).

- **MinIO Console**: http://localhost:9001 (admin/minioadmin)
- **Lakekeeper API**: http://localhost:8181

[Read more](catalog/README.md)

### [Transactional Database](transactional-db/)

Postgres with PGD (Bi-Directional Replication) and PGAA extensions.

- **Connection**: `psql -h localhost -p 7432 -U postgres -d demo`
- **Password**: `secret`

[Read more](transactional-db/README.md)

### [Spark Cluster](spark/)

Apache Spark with Connect endpoint, Iceberg support, and optional RAPIDS GPU acceleration.

- **Spark Master UI**: http://localhost:8080
- **Spark Connect**: `sc://localhost:15002`
- **Spark App UI**: http://localhost:4040

[Read more](spark/README.md)

### [Analytics Database](analytics-db/)

WarehousePG (Greenplum 7.x fork) with PGAA extension for analytics queries.

- **Connection**: `psql -h localhost -p 5432 -U gpadmin -d demo`
- **Password**: `password`

[Read more](analytics-db/README.md)

## Configuration

All components are configured via [`demo-config.toml`](demo-config.toml).

### Validate Configuration

```bash
python3 scripts/config_validator.py --validate
python3 scripts/config_validator.py --display
```

### Key Configuration Sections

```toml
[catalog]
name = "demo_catalog"           # Catalog name used in PGAA
url = "http://lakekeeper:8181"  # REST Catalog endpoint

[object_store]
type = "minio"
endpoint = "http://minio:9000"
bucket = "warehouse"

[spark]
enable_rapids = false           # Toggle GPU acceleration
connect_url = "sc://spark-master:15002"

[database.transactional]
host = "pgd"
port = 5432

[database.analytics]
host = "whpg"
port = 5432
```

### Using a Remote Catalog

To use a remote Iceberg REST Catalog instead of local Lakekeeper:

1. Edit `demo-config.toml`:

   ```toml
   [catalog]
   url = "https://your-catalog.example.com/api/iceberg"
   warehouse = "your-warehouse-id"
   token = "your-auth-token"
   ```

2. Update object store settings:

   ```toml
   [object_store]
   type = "s3"
   endpoint = "https://s3.amazonaws.com"
   bucket = "your-bucket"
   access_key = "your-access-key"
   secret_key = "your-secret-key"
   ```

3. Rebuild and restart components:
   ```bash
   ./scripts/start-demo.sh stop
   docker-compose -f transactional-db/docker-compose.yml down -v
   docker-compose -f analytics-db/docker-compose.yml down -v
   ./scripts/start-demo.sh start
   ```

## Usage Examples

### Query from PGD (Transactional)

```sql
-- Connect to PGD
psql -h localhost -p 7432 -U postgres -d demo

-- Query transactional data
SET bdr.prefer_analytics_engine = false;
SELECT country_name, COUNT(*) FROM demo.sales s
JOIN demo.countries c ON s.country_code = c.country_code
GROUP BY country_name;

-- Query analytics data (Iceberg)
SET bdr.prefer_analytics_engine = true;
SELECT country_name, COUNT(*) FROM demo.sales s
JOIN demo.countries c ON s.country_code = c.country_code
GROUP BY country_name;
```

### Query from WarehousePG (Analytics)

```sql
-- Connect to WarehousePG
psql -h localhost -p 5432 -U gpadmin -d demo

-- Use Datafusion engine
SET pgaa.executor_engine = 'seafowl';
SELECT category, SUM(revenue) FROM demo.sales s
JOIN demo.products p ON s.product_id = p.product_id
GROUP BY category;

-- Use Spark Connect engine
SET pgaa.executor_engine = 'spark_connect';
SET pgaa.spark_connect_url = 'sc://172.17.0.1:15002';
SELECT category, SUM(revenue) FROM demo.sales s
JOIN demo.products p ON s.product_id = p.product_id
GROUP BY category;
```

## Data Schema

The demo includes three dimension tables and one fact table:

```sql
-- Countries (20 countries with realistic sales distribution)
demo.countries (country_code, country_name, region, population, gdp_usd)

-- Products (100 products across 5 categories)
demo.products (product_id, product_name, category, unit_price, cost_price)

-- Customers (1,000 customers)
demo.customers (customer_id, customer_name, email, country_code, registration_date)

-- Sales (10,000 transactions)
demo.sales (sale_id, customer_id, product_id, country_code, quantity,
            unit_price, revenue, cost, profit, sale_date)
```

No foreign keys are used for demo simplicity.

## Docker Context Management

This project supports both local and remote Docker contexts.

### Check Current Context

```bash
docker context show
```

### Local macOS Context

```bash
docker context use desktop-linux
```

### Remote EC2 Context (if configured)

```bash
docker context use ec2box
```

For remote contexts, ensure your SSH configuration is set up correctly. This assumes the EC2 box is accessible at `$REMOTE_DOCKER_HOST`.

## Network Configuration

The stack uses a Docker bridge network named `converged-analytics-network`. All components communicate via this network.

### Bridge IP for Spark Connect

When WarehousePG needs to reach Spark Connect on the host:

```sql
SET pgaa.spark_connect_url = 'sc://172.17.0.1:15002';
```

This uses the Docker bridge IP (`172.17.0.1`) to access the Spark Connect port exposed on the host.

## Management Commands

### Start/Stop/Restart

```bash
# Start all components
./scripts/start-demo.sh start

# Stop all components
./scripts/start-demo.sh stop

# Restart all components
./scripts/start-demo.sh restart

# Show status
./scripts/start-demo.sh status
```

### Component Logs

```bash
# View all logs
docker-compose -f catalog/docker-compose.yml logs -f
docker-compose -f transactional-db/docker-compose.yml logs -f
docker-compose -f spark/docker-compose.yml logs -f
docker-compose -f analytics-db/docker-compose.yml logs -f

# View specific service logs
docker logs -f pgd
docker logs -f whpg
docker logs -f spark-connect
```

### Clean Up

```bash
# Stop all components
./scripts/start-demo.sh stop

# Remove all volumes (WARNING: destroys data)
docker-compose -f catalog/docker-compose.yml down -v
docker-compose -f transactional-db/docker-compose.yml down -v
docker-compose -f spark/docker-compose.yml down -v
docker-compose -f analytics-db/docker-compose.yml down -v
```

## Enabling RAPIDS GPU Acceleration

### Prerequisites

1. NVIDIA GPU with CUDA support
2. NVIDIA Driver installed
3. NVIDIA Container Toolkit installed

### Enable RAPIDS

1. Edit `demo-config.toml`:

   ```toml
   [spark]
   enable_rapids = true
   ```

2. Uncomment GPU configuration in `spark/docker-compose.yml`:

   ```yaml
   deploy:
     resources:
       reservations:
         devices:
           - driver: nvidia
             capabilities: [gpu]
             device_ids: ["all"]
   ```

3. Rebuild and restart Spark:
   ```bash
   cd spark
   docker-compose down
   docker-compose up -d --build
   ```

### Verify GPU

```bash
# Check GPU availability
docker exec spark-worker nvidia-smi

# Toggle RAPIDS in queries
psql -h localhost -p 5432 -U gpadmin -d demo
SET pgaa.spark_connect_extra_config = '{"spark.rapids.sql.enabled": "false"}';  # Disable
RESET pgaa.spark_connect_extra_config;  # Enable
```

## Troubleshooting

### Component won't start

Check logs:

```bash
docker-compose -f <component>/docker-compose.yml logs
```

### Configuration validation fails

The entrypoints validate that runtime configuration matches `demo-config.toml`. If validation fails:

1. Update `demo-config.toml` to match the running configuration, OR
2. Remove volumes and rebuild:
   ```bash
   docker-compose -f <component>/docker-compose.yml down -v
   docker-compose -f <component>/docker-compose.yml up -d --build
   ```

### Cannot connect to database

Ensure the service is healthy:

```bash
docker ps
docker inspect <container-name>
```

### Spark Connect timeout

Verify Spark Connect is running and accessible:

```bash
curl -v sc://localhost:15002
docker logs spark-connect
```

## Python Development

All Python scripts use `uv` for dependency management.

### Setup

```bash
cd scripts
uv venv
source .venv/bin/activate
uv pip install -e .
```

### Development Tools

```bash
# Type checking
uv run mypy scripts/*.py

# Code formatting
uv run black scripts/

# Run tests
uv run pytest
```

## Examples Directory

See the [`examples/`](examples/) directory for additional reference code:

- [example-code-pgd-with-pgaa.md](examples/example-code-pgd-with-pgaa.md) - PGD + PGAA setup patterns
- [example-code-with-pgaa-inside-warehousepg.md](examples/example-code-with-pgaa-inside-warehousepg.md) - WHPG + PGAA patterns
- [example-code-running-whpg-pgaa-demo.md](examples/example-code-running-whpg-pgaa-demo.md) - WHPG demo walkthrough
- [example-code-rapids-with-iceberg.md](examples/example-code-rapids-with-iceberg.md) - Spark RAPIDS + Iceberg patterns
- [example-code-spark-rapids-tutorial.md](examples/example-code-spark-rapids-tutorial.md) - Spark RAPIDS tutorial

## Project Structure

```
.
├── demo-config.toml              # Central configuration
├── README.md                     # This file
├── AGENTS.md                     # Development context and rules
├── spec.md                       # Technical specifications
├── catalog/                      # Lakekeeper + MinIO
│   ├── docker-compose.yml
│   └── README.md
├── transactional-db/             # PGD + PGAA
│   ├── Dockerfile
│   ├── docker-compose.yml
│   ├── docker-entrypoint.sh
│   ├── .env.example
│   └── README.md
├── spark/                        # Spark Connect cluster
│   ├── Dockerfile
│   ├── docker-compose.yml
│   ├── spark-entrypoint.sh
│   ├── spark-defaults.conf
│   └── README.md
├── analytics-db/                 # WarehousePG + PGAA
│   ├── Dockerfile
│   ├── docker-compose.yml
│   ├── docker-entrypoint.sh
│   ├── init_system.sh
│   ├── gpinitsystem_config
│   ├── hostfile_gpinitsystem
│   ├── .env.example
│   └── README.md
├── scripts/                      # Helper scripts
│   ├── pyproject.toml
│   ├── config_validator.py       # Validate/display config
│   ├── generate_data.py          # Generate and load demo data
│   ├── query_examples.py         # Example queries
│   └── start-demo.sh             # Orchestration script
└── examples/                     # Reference code and patterns
```

## License

This demo is provided as-is for educational and demonstration purposes.

## Support

For issues or questions:

1. Check component README files
2. Review logs with `docker-compose logs`
3. Verify configuration with `python3 scripts/config_validator.py`
4. Consult the [examples/](examples/) directory for reference patterns

## Contributing

This is a reference implementation. For production use, consider:

- Security hardening (credentials, network policies)
- High availability configuration
- Resource sizing for your workload
- Monitoring and alerting setup
- Backup and disaster recovery procedures
