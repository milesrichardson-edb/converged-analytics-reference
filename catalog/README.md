# Catalog Component: Lakekeeper + MinIO

This component provides the Iceberg REST Catalog (Lakekeeper) and S3-compatible object storage (MinIO) for the converged analytics demo.

## Components

- **MinIO**: S3-compatible object storage for Iceberg data files
- **Lakekeeper**: Iceberg REST Catalog server (v0.10.3) for metadata management
- **Lakekeeper Postgres**: PostgreSQL 17.4 database for Lakekeeper metadata
- **Lakekeeper Migrate**: Database migration service (runs once on startup)
- **Lakekeeper Bootstrap**: EULA acceptance service (runs once on startup)
- **Create Buckets**: MinIO bucket initialization (creates `warehouse` bucket)

## Quick Start

```bash
# Start the catalog stack
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f lakekeeper

# Stop the stack
docker-compose down
```

## Accessing Services

- **MinIO Console**: http://localhost:9001 (minioadmin/minioadmin)
- **MinIO API**: http://localhost:9000
- **Lakekeeper REST API**: http://localhost:8181
- **Lakekeeper Health Check**: http://localhost:8181/catalog/v1/config (or use healthcheck command)
- **Lakekeeper Postgres**: localhost:9054 (postgres/password)

## Configuration

The catalog configuration is defined in `/demo-config.toml`:

```toml
[catalog]
name = "demo_catalog"
type = "iceberg-rest"
url = "http://lakekeeper:8181"
warehouse = "demo-warehouse"

[object_store]
type = "minio"
endpoint = "http://minio:9000"
bucket = "warehouse"
access_key = "minioadmin"
secret_key = "minioadmin"
```

## Verification

After startup, verify the services are running:

```bash
# Check all container status
docker-compose ps

# Check Lakekeeper health (should return 200)
docker exec lakekeeper /home/nonroot/lakekeeper healthcheck

# Check if warehouse bucket was created
docker exec -it minio mc ls local/

# Check Lakekeeper database
docker exec -it lakekeeper-postgres psql -U postgres -d lakekeeper -c "\dt"
```

## Network

This component creates the `converged-analytics-network` bridge network that other components will join.

## Volumes

- `minio-data`: Persistent storage for MinIO data
- `lakekeeper-db-data`: Persistent storage for Lakekeeper metadata

## Troubleshooting

```bash
# Check if MinIO is healthy
docker exec minio mc admin info local

# Check Lakekeeper logs
docker-compose logs lakekeeper

# Check migration logs
docker-compose logs lakekeeper-migrate

# Check if bucket was created
docker-compose logs createbuckets

# Check if EULA was accepted
docker-compose logs lakekeeper-bootstrap

# Restart services
docker-compose restart lakekeeper

# Clean restart (removes volumes - WARNING: deletes all data)
docker-compose down -v
docker-compose up -d
```

## Notes

- Lakekeeper uses `allowall` authorization backend for demo purposes (no authentication required)
- The database migration service (`lakekeeper-migrate`) runs once on startup and exits
- MinIO bucket creation (`createbuckets`) runs once on startup and exits
- Lakekeeper waits for both migration and bucket creation to complete before starting
