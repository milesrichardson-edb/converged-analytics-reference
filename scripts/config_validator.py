#!/usr/bin/env python3
"""
Configuration validator and updater for converged analytics demo.

This script reads, validates, and optionally updates the demo-config.toml file.
"""

import sys
from pathlib import Path
from typing import Any, Dict, Optional

try:
    import tomli
except ImportError:
    print("Error: tomli not installed. Run: uv pip install tomli", file=sys.stderr)
    sys.exit(1)

try:
    from rich.console import Console
    from rich.table import Table
except ImportError:
    print("Error: rich not installed. Run: uv pip install rich", file=sys.stderr)
    sys.exit(1)


console = Console()


def load_config(config_path: Path) -> Dict[str, Any]:
    """Load TOML configuration file."""
    if not config_path.exists():
        console.print(f"[red]Error: Configuration file not found: {config_path}[/red]")
        sys.exit(1)

    with open(config_path, "rb") as f:
        return tomli.load(f)


def validate_config(config: Dict[str, Any]) -> bool:
    """Validate configuration structure and required fields."""
    errors = []

    # Required top-level sections
    required_sections = [
        "catalog",
        "object_store",
        "spark",
        "network",
        "database",
        "demo_data",
    ]
    for section in required_sections:
        if section not in config:
            errors.append(f"Missing required section: [{section}]")

    # Validate catalog section
    if "catalog" in config:
        required_catalog_fields = ["name", "type", "url", "warehouse"]
        for field in required_catalog_fields:
            if field not in config["catalog"]:
                errors.append(f"Missing required field: catalog.{field}")

    # Validate object_store section
    if "object_store" in config:
        required_store_fields = ["type", "endpoint", "bucket", "access_key", "secret_key"]
        for field in required_store_fields:
            if field not in config["object_store"]:
                errors.append(f"Missing required field: object_store.{field}")

    # Validate spark section
    if "spark" in config:
        required_spark_fields = ["enable_rapids", "connect_url", "version"]
        for field in required_spark_fields:
            if field not in config["spark"]:
                errors.append(f"Missing required field: spark.{field}")

    # Validate database sections
    if "database" in config:
        if "transactional" not in config["database"]:
            errors.append("Missing required section: database.transactional")
        if "analytics" not in config["database"]:
            errors.append("Missing required section: database.analytics")

    if errors:
        console.print("[red]Configuration validation failed:[/red]")
        for error in errors:
            console.print(f"  [red]✗[/red] {error}")
        return False

    console.print("[green]✓ Configuration validation passed[/green]")
    return True


def display_config(config: Dict[str, Any]) -> None:
    """Display configuration in a formatted table."""
    # Catalog table
    table = Table(title="Catalog Configuration", show_header=True, header_style="bold magenta")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")

    catalog = config.get("catalog", {})
    table.add_row("Name", catalog.get("name", ""))
    table.add_row("Type", catalog.get("type", ""))
    table.add_row("URL", catalog.get("url", ""))
    table.add_row("Warehouse", catalog.get("warehouse", ""))
    table.add_row("Token", "***" if catalog.get("token") else "(not set)")

    console.print(table)

    # Object Store table
    table = Table(title="Object Store Configuration", show_header=True, header_style="bold magenta")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")

    store = config.get("object_store", {})
    table.add_row("Type", store.get("type", ""))
    table.add_row("Endpoint", store.get("endpoint", ""))
    table.add_row("Bucket", store.get("bucket", ""))
    table.add_row("Access Key", store.get("access_key", ""))
    table.add_row("Secret Key", "***" if store.get("secret_key") else "(not set)")

    console.print(table)

    # Spark table
    table = Table(title="Spark Configuration", show_header=True, header_style="bold magenta")
    table.add_column("Setting", style="cyan")
    table.add_column("Value", style="green")

    spark = config.get("spark", {})
    table.add_row("RAPIDS Enabled", str(spark.get("enable_rapids", False)))
    table.add_row("Connect URL", spark.get("connect_url", ""))
    table.add_row("Version", spark.get("version", ""))
    table.add_row("Scala Version", spark.get("scala_version", ""))
    table.add_row("Iceberg Version", spark.get("iceberg_version", ""))

    console.print(table)

    # Database table
    table = Table(title="Database Configuration", show_header=True, header_style="bold magenta")
    table.add_column("Component", style="cyan")
    table.add_column("Host", style="green")
    table.add_column("Port", style="green")
    table.add_column("Database", style="green")

    db = config.get("database", {})
    txn = db.get("transactional", {})
    analytics = db.get("analytics", {})

    table.add_row(
        "Transactional (PGD)",
        txn.get("host", ""),
        str(txn.get("port", "")),
        txn.get("database", ""),
    )
    table.add_row(
        "Analytics (WHPG)",
        analytics.get("host", ""),
        str(analytics.get("port", "")),
        analytics.get("database", ""),
    )

    console.print(table)


def get_config_value(config: Dict[str, Any], key: str) -> Optional[Any]:
    """Get a nested configuration value using dot notation."""
    keys = key.split(".")
    value: Any = config
    for k in keys:
        if isinstance(value, dict) and k in value:
            value = value[k]
        else:
            return None
    return value


def main() -> None:
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Validate and manage demo-config.toml configuration"
    )
    parser.add_argument(
        "--config",
        "-c",
        type=Path,
        default=Path(__file__).parent.parent / "demo-config.toml",
        help="Path to configuration file (default: ../demo-config.toml)",
    )
    parser.add_argument("--validate", "-v", action="store_true", help="Validate configuration only")
    parser.add_argument("--display", "-d", action="store_true", help="Display configuration")
    parser.add_argument(
        "--get", "-g", type=str, help="Get configuration value (e.g., catalog.name)"
    )

    args = parser.parse_args()

    # Load configuration
    config = load_config(args.config)

    # Validate
    if args.validate or not (args.display or args.get):
        if not validate_config(config):
            sys.exit(1)

    # Display
    if args.display or not (args.validate or args.get):
        display_config(config)

    # Get specific value
    if args.get:
        value = get_config_value(config, args.get)
        if value is None:
            console.print(f"[red]Error: Key not found: {args.get}[/red]")
            sys.exit(1)
        console.print(value)


if __name__ == "__main__":
    main()
