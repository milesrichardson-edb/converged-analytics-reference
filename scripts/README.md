# Scripts README

This directory contains Python helper scripts for managing the converged analytics demo.

## Installation

All scripts use `uv` for dependency management:

```bash
# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment and install dependencies
cd scripts
uv venv
source .venv/bin/activate  # On macOS/Linux
# Or on Windows: .venv\Scripts\activate

# Install dependencies
uv pip install -e .
```

## Scripts

### config_validator.py

Validate and display the demo configuration.

```bash
# Validate configuration
python3 config_validator.py --validate

# Display configuration
python3 config_validator.py --display

# Get specific value
python3 config_validator.py --get catalog.name
```

### generate_data.py

Generate synthetic demo data and load into PGD.

```bash
# Create tables and load data
python3 generate_data.py --all

# Only create tables
python3 generate_data.py --create-tables

# Only load data (tables must exist)
python3 generate_data.py --load-data

# Append more data to existing tables (useful for testing with larger datasets)
python3 generate_data.py --append

# Use scale factor to generate larger datasets (e.g., 10x the configured data)
python3 generate_data.py --all --scale-factor 10
python3 generate_data.py --append --scale-factor 5
```

The data generator creates (with default scale factor of 1.0):

- 20 countries with realistic sales distribution
- 100 products across 5 categories
- 1,000 customers
- 10,000 sales transactions

**Scale Factor**: Use `--scale-factor` or `-s` to multiply the number of products, customers, and sales generated. For example, `--scale-factor 10` will generate 1,000 products, 10,000 customers, and 100,000 sales.

**Note**: Use `--append` to add more data without dropping existing tables. You can run this multiple times to grow your dataset incrementally.

### wait_for_replication.py

Wait for PGD analytics replication to complete.

```bash
# Wait for all WAL records to be replicated to Iceberg
python3 wait_for_replication.py
```

This script blocks until the analytics replication slot has confirmed all pending WAL records have been written to Iceberg. Useful in scripts when you need to ensure data is available in analytics before proceeding with queries.

### setup_whpg.py

Setup WarehousePG with PGAA catalogs and tables.

```bash
# Setup with local Lakekeeper catalog
python3 setup_whpg.py --local-catalog

# Setup Delta tables from public S3
python3 setup_whpg.py --delta-tables

# Setup both
python3 setup_whpg.py --local-catalog --delta-tables
```

**Local catalog mode** (`--local-catalog`):

- Adds Lakekeeper Iceberg REST catalog (from demo-config.toml)
- Creates `demo` schema
- Creates Iceberg tables: `demo.countries`, `demo.products`, `demo.customers`, `demo.sales`
- These tables will be populated by PGD replication

**Delta tables mode** (`--delta-tables`):

- Creates storage location for public S3 bucket
- Creates `sample_delta_tpch_sf_1` schema
- Creates read-only Delta/Parquet tables from EDB public dataset
- Tables: `customer`, `lineitem`, `nation`, `orders`, `part`, `partsupp`, `region`, `supplier`

### query_examples.py

Run example queries demonstrating different execution engines.

```bash
# Run all examples
python3 query_examples.py --all

# Run specific examples
python3 query_examples.py --pgd-transactional  # PGD transactional engine
python3 query_examples.py --pgd-analytics      # PGD analytics engine (Iceberg)
python3 query_examples.py --whpg-datafusion    # WHPG with Datafusion
python3 query_examples.py --whpg-spark         # WHPG with Spark Connect
```

### start-demo.sh

Orchestration script to start/stop all components.

```bash
# Start all components in order
./start-demo.sh start

# Stop all components
./start-demo.sh stop

# Restart all components
./start-demo.sh restart

# Show status
./start-demo.sh status
```

## Development

### Type Checking

```bash
uv run mypy scripts/*.py
```

### Code Formatting

```bash
uv run black scripts/
```

### Testing

```bash
uv run pytest
```

## Dependencies

- `tomli`: TOML configuration parsing
- `psycopg2-binary`: PostgreSQL database adapter
- `faker`: Synthetic data generation
- `click`: Command-line interface
- `rich`: Terminal formatting and tables

Development dependencies:

- `mypy`: Type checking
- `black`: Code formatting
- `pytest`: Testing framework
