#!/usr/bin/env python3
"""
Synthetic data generator for converged analytics demo.

Generates procedural synthetic data (sales, customers, products) and loads into PGD.
"""

import random
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Tuple

try:
    import tomli
except ImportError:
    print("Error: tomli not installed. Run: uv pip install tomli", file=sys.stderr)
    sys.exit(1)

try:
    import psycopg2
    from psycopg2.extras import execute_batch
except ImportError:
    print("Error: psycopg2 not installed. Run: uv pip install psycopg2-binary", file=sys.stderr)
    sys.exit(1)

try:
    from faker import Faker
except ImportError:
    print("Error: faker not installed. Run: uv pip install faker", file=sys.stderr)
    sys.exit(1)

try:
    from rich.console import Console
    from rich.progress import track
except ImportError:
    print("Error: rich not installed. Run: uv pip install rich", file=sys.stderr)
    sys.exit(1)


console = Console()


# Seed data: countries with realistic weights for sales distribution
COUNTRIES = [
    ("United States", 25.0),
    ("China", 20.0),
    ("Japan", 8.0),
    ("Germany", 7.0),
    ("United Kingdom", 6.0),
    ("France", 5.0),
    ("India", 5.0),
    ("Italy", 4.0),
    ("Canada", 4.0),
    ("South Korea", 3.0),
    ("Spain", 2.5),
    ("Australia", 2.5),
    ("Brazil", 2.0),
    ("Mexico", 1.5),
    ("Netherlands", 1.0),
    ("Saudi Arabia", 1.0),
    ("Switzerland", 0.8),
    ("Singapore", 0.7),
    ("Sweden", 0.5),
    ("Norway", 0.5),
]

# Product categories and example products
PRODUCT_CATEGORIES = {
    "Electronics": ["Laptop", "Smartphone", "Tablet", "Smartwatch", "Headphones", "Camera"],
    "Clothing": ["T-Shirt", "Jeans", "Jacket", "Sneakers", "Dress", "Sweater"],
    "Home & Garden": ["Sofa", "Dining Table", "Lamp", "Rug", "Plant Pot", "Curtains"],
    "Sports": ["Running Shoes", "Yoga Mat", "Bicycle", "Tennis Racket", "Dumbbells", "Backpack"],
    "Books": ["Fiction Novel", "Biography", "Cookbook", "Self-Help", "Textbook", "Comic Book"],
}


def load_config(config_path: Path) -> Dict[str, Any]:
    """Load TOML configuration file."""
    with open(config_path, "rb") as f:
        return tomli.load(f)


def get_db_connection(config: Dict[str, Any], analytics: bool = False) -> Any:
    """Get database connection to PGD or WHPG."""
    db_config = config["database"]["analytics" if analytics else "transactional"]

    # For PGD, use port 7432 (exposed port)
    port = db_config["port"] if analytics else 7432

    return psycopg2.connect(
        host="localhost",
        port=port,
        database=db_config["database"],
        user=db_config["user"],
        password=db_config["password"],
    )


def create_tables(conn: Any, config: Dict[str, Any], drop_existing: bool = True) -> None:
    """Create demo tables with analytics replication enabled.

    Args:
        conn: Database connection
        config: Configuration dictionary
        drop_existing: If True, drop existing tables before creating. If False, skip if tables exist.
    """
    catalog_name = config["catalog"]["name"]

    with conn.cursor() as cur:
        # Create demo schema
        cur.execute("CREATE SCHEMA IF NOT EXISTS demo;")

        if drop_existing:
            # Countries dimension table
            cur.execute("DROP TABLE IF EXISTS demo.countries CASCADE;")
            cur.execute(
                """
                CREATE TABLE demo.countries (
                    country_code SERIAL PRIMARY KEY,
                    country_name VARCHAR(100) NOT NULL,
                    region VARCHAR(50),
                    population BIGINT,
                    gdp_usd BIGINT
                ) WITH (pgd.replicate_to_analytics = true);
            """
            )

            # Products dimension table
            cur.execute("DROP TABLE IF EXISTS demo.products CASCADE;")
            cur.execute(
                """
                CREATE TABLE demo.products (
                    product_id SERIAL PRIMARY KEY,
                    product_name VARCHAR(200) NOT NULL,
                    category VARCHAR(100) NOT NULL,
                    unit_price DECIMAL(10, 2) NOT NULL,
                    cost_price DECIMAL(10, 2) NOT NULL
                ) WITH (pgd.replicate_to_analytics = true);
            """
            )

            # Customers dimension table
            cur.execute("DROP TABLE IF EXISTS demo.customers CASCADE;")
            cur.execute(
                """
                CREATE TABLE demo.customers (
                    customer_id SERIAL PRIMARY KEY,
                    customer_name VARCHAR(200) NOT NULL,
                    email VARCHAR(200),
                    country_code INT,
                    registration_date DATE NOT NULL
                ) WITH (pgd.replicate_to_analytics = true);
            """
            )

            # Sales fact table (no foreign keys for demo simplicity)
            cur.execute("DROP TABLE IF EXISTS demo.sales CASCADE;")
            cur.execute(
                """
                CREATE TABLE demo.sales (
                    sale_id SERIAL,
                    customer_id INT NOT NULL,
                    product_id INT NOT NULL,
                    country_code INT NOT NULL,
                    quantity INT NOT NULL,
                    unit_price DECIMAL(10, 2) NOT NULL,
                    revenue DECIMAL(12, 2) NOT NULL,
                    cost DECIMAL(12, 2) NOT NULL,
                    profit DECIMAL(12, 2) NOT NULL,
                    sale_date DATE NOT NULL,
                    PRIMARY KEY (sale_id, sale_date)
                ) WITH (pgd.replicate_to_analytics = true);
            """
            )
        else:
            # Create tables only if they don't exist
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS demo.countries (
                    country_code SERIAL PRIMARY KEY,
                    country_name VARCHAR(100) NOT NULL,
                    region VARCHAR(50),
                    population BIGINT,
                    gdp_usd BIGINT
                ) WITH (pgd.replicate_to_analytics = true);
            """
            )

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS demo.products (
                    product_id SERIAL PRIMARY KEY,
                    product_name VARCHAR(200) NOT NULL,
                    category VARCHAR(100) NOT NULL,
                    unit_price DECIMAL(10, 2) NOT NULL,
                    cost_price DECIMAL(10, 2) NOT NULL
                ) WITH (pgd.replicate_to_analytics = true);
            """
            )

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS demo.customers (
                    customer_id SERIAL PRIMARY KEY,
                    customer_name VARCHAR(200) NOT NULL,
                    email VARCHAR(200),
                    country_code INT,
                    registration_date DATE NOT NULL
                ) WITH (pgd.replicate_to_analytics = true);
            """
            )

            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS demo.sales (
                    sale_id SERIAL,
                    customer_id INT NOT NULL,
                    product_id INT NOT NULL,
                    country_code INT NOT NULL,
                    quantity INT NOT NULL,
                    unit_price DECIMAL(10, 2) NOT NULL,
                    revenue DECIMAL(12, 2) NOT NULL,
                    cost DECIMAL(12, 2) NOT NULL,
                    profit DECIMAL(12, 2) NOT NULL,
                    sale_date DATE NOT NULL,
                    PRIMARY KEY (sale_id, sale_date)
                ) WITH (pgd.replicate_to_analytics = true);
            """
            )

        conn.commit()

    if drop_existing:
        console.print("[green]✓ Created tables with analytics replication enabled[/green]")
    else:
        console.print("[green]✓ Tables ready (existing tables preserved)[/green]")


def generate_countries(config: Dict[str, Any]) -> List[Tuple[str, str, int, int]]:
    """Generate country dimension data."""
    fake = Faker()
    fake.seed_instance(config["demo_data"]["random_seed"])
    random.seed(config["demo_data"]["random_seed"])

    countries_data = []
    for country_name, _ in COUNTRIES:
        # Assign regions
        if country_name in [
            "United States",
            "Canada",
            "Mexico",
            "Brazil",
        ]:
            region = "Americas"
        elif country_name in [
            "United Kingdom",
            "Germany",
            "France",
            "Italy",
            "Spain",
            "Netherlands",
            "Switzerland",
            "Sweden",
            "Norway",
        ]:
            region = "Europe"
        elif country_name in ["China", "Japan", "India", "South Korea", "Singapore"]:
            region = "Asia-Pacific"
        else:
            region = "Other"

        population = random.randint(5_000_000, 1_400_000_000)
        gdp_usd = random.randint(100_000_000_000, 25_000_000_000_000)

        countries_data.append((country_name, region, population, gdp_usd))

    return countries_data


def generate_products(
    config: Dict[str, Any], scale_factor: float = 1.0
) -> List[Tuple[str, str, float, float]]:
    """Generate product dimension data."""
    fake = Faker()
    fake.seed_instance(config["demo_data"]["random_seed"])
    random.seed(config["demo_data"]["random_seed"])

    num_products = int(config["demo_data"]["num_products"] * scale_factor)
    products_data = []

    for _ in range(num_products):
        category = random.choice(list(PRODUCT_CATEGORIES.keys()))
        base_name = random.choice(PRODUCT_CATEGORIES[category])

        # Add variation
        if random.random() > 0.7:
            variation = random.choice(["Pro", "Plus", "Premium", "Deluxe", "Standard"])
            product_name = f"{base_name} {variation}"
        else:
            product_name = base_name

        # Price based on category
        if category == "Electronics":
            unit_price = round(random.uniform(200, 2000), 2)
        elif category == "Clothing":
            unit_price = round(random.uniform(20, 200), 2)
        elif category == "Home & Garden":
            unit_price = round(random.uniform(50, 1000), 2)
        elif category == "Sports":
            unit_price = round(random.uniform(30, 500), 2)
        else:  # Books
            unit_price = round(random.uniform(10, 50), 2)

        cost_price = round(unit_price * random.uniform(0.4, 0.7), 2)

        products_data.append((product_name, category, unit_price, cost_price))

    return products_data


def generate_customers(
    config: Dict[str, Any], num_countries: int, scale_factor: float = 1.0
) -> List[Tuple[str, str, int, str]]:
    """Generate customer dimension data."""
    fake = Faker()
    fake.seed_instance(config["demo_data"]["random_seed"])
    random.seed(config["demo_data"]["random_seed"])

    num_customers = int(config["demo_data"]["num_customers"] * scale_factor)
    customers_data = []

    start_date = datetime.strptime(config["demo_data"]["start_date"], "%Y-%m-%d")
    end_date = datetime.strptime(config["demo_data"]["end_date"], "%Y-%m-%d")
    date_range = (end_date - start_date).days

    for _ in range(num_customers):
        customer_name = fake.name()
        email = fake.email()
        country_code = random.randint(1, num_countries)

        # Registration date
        reg_date = start_date + timedelta(days=random.randint(0, date_range))
        registration_date = reg_date.strftime("%Y-%m-%d")

        customers_data.append((customer_name, email, country_code, registration_date))

    return customers_data


def generate_sales(
    config: Dict[str, Any],
    num_customers: int,
    num_products: int,
    num_countries: int,
    scale_factor: float = 1.0,
) -> List[Tuple[int, int, int, int, float, float, float, float, str]]:
    """Generate sales fact data."""
    random.seed(config["demo_data"]["random_seed"])

    num_sales = int(config["demo_data"]["num_sales"] * scale_factor)
    sales_data = []

    start_date = datetime.strptime(config["demo_data"]["start_date"], "%Y-%m-%d")
    end_date = datetime.strptime(config["demo_data"]["end_date"], "%Y-%m-%d")
    date_range = (end_date - start_date).days

    # Prepare country weights for weighted random selection
    country_weights = [weight for _, weight in COUNTRIES[:num_countries]]

    for _ in range(num_sales):
        customer_id = random.randint(1, num_customers)
        product_id = random.randint(1, num_products)

        # Weighted country selection
        country_code = random.choices(range(1, num_countries + 1), weights=country_weights, k=1)[0]

        quantity = random.randint(1, 10)

        # Price variation (±10% from list price)
        unit_price = round(random.uniform(50, 500) * random.uniform(0.9, 1.1), 2)
        cost = round(unit_price * random.uniform(0.4, 0.7), 2)

        revenue = round(quantity * unit_price, 2)
        total_cost = round(quantity * cost, 2)
        profit = round(revenue - total_cost, 2)

        # Sale date
        sale_date = start_date + timedelta(days=random.randint(0, date_range))
        sale_date_str = sale_date.strftime("%Y-%m-%d")

        sales_data.append(
            (
                customer_id,
                product_id,
                country_code,
                quantity,
                unit_price,
                revenue,
                total_cost,
                profit,
                sale_date_str,
            )
        )

    return sales_data


def load_data(conn: Any, config: Dict[str, Any], scale_factor: float = 1.0) -> None:
    """Load generated data into database."""
    console.print("[yellow]Generating data...[/yellow]")

    # Generate dimension data
    countries = generate_countries(config)
    products = generate_products(config, scale_factor)
    customers = generate_customers(config, len(countries), scale_factor)
    sales = generate_sales(config, len(customers), len(products), len(countries), scale_factor)

    console.print(f"[green]✓ Generated {len(countries)} countries[/green]")
    console.print(f"[green]✓ Generated {len(products)} products[/green]")
    console.print(f"[green]✓ Generated {len(customers)} customers[/green]")
    console.print(f"[green]✓ Generated {len(sales)} sales transactions[/green]")

    # Load data
    with conn.cursor() as cur:
        console.print("[yellow]Loading countries...[/yellow]")
        execute_batch(
            cur,
            "INSERT INTO demo.countries (country_name, region, population, gdp_usd) VALUES (%s, %s, %s, %s)",
            countries,
        )

        console.print("[yellow]Loading products...[/yellow]")
        execute_batch(
            cur,
            "INSERT INTO demo.products (product_name, category, unit_price, cost_price) VALUES (%s, %s, %s, %s)",
            products,
        )

        console.print("[yellow]Loading customers...[/yellow]")
        execute_batch(
            cur,
            "INSERT INTO demo.customers (customer_name, email, country_code, registration_date) VALUES (%s, %s, %s, %s)",
            customers,
        )

        console.print("[yellow]Loading sales...[/yellow]")
        for batch_sales in track(
            [sales[i : i + 1000] for i in range(0, len(sales), 1000)],
            description="Loading sales batches",
        ):
            execute_batch(
                cur,
                """
                INSERT INTO demo.sales
                (customer_id, product_id, country_code, quantity, unit_price, revenue, cost, profit, sale_date)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                batch_sales,
            )

        conn.commit()

    console.print("[green]✓ Data loaded successfully[/green]")

    # Wait for replication
    console.print("[yellow]Waiting for analytics replication...[/yellow]")
    with conn.cursor() as cur:
        cur.execute("SELECT bdr.wait_slot_confirm_lsn(NULL, NULL);")

    console.print("[green]✓ Analytics replication complete[/green]")


def main() -> None:
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Generate and load demo data")
    parser.add_argument(
        "--config",
        "-c",
        type=Path,
        default=Path(__file__).parent.parent / "demo-config.toml",
        help="Path to configuration file",
    )
    parser.add_argument(
        "--create-tables", action="store_true", help="Create tables (drops existing tables)"
    )
    parser.add_argument("--load-data", action="store_true", help="Load generated data")
    parser.add_argument(
        "--append",
        action="store_true",
        help="Append data to existing tables (don't drop tables, just add more data)",
    )
    parser.add_argument("--all", action="store_true", help="Create tables and load data")
    parser.add_argument(
        "--scale-factor",
        "-s",
        type=float,
        default=1.0,
        help="Scale factor for data generation (default: 1.0). Multiplies number of products, customers, and sales.",
    )

    args = parser.parse_args()

    if not (args.create_tables or args.load_data or args.all or args.append):
        parser.print_help()
        sys.exit(1)

    # Load configuration
    config = load_config(args.config)

    # Connect to PGD
    console.print("[yellow]Connecting to PGD...[/yellow]")
    conn = get_db_connection(config)
    console.print("[green]✓ Connected to PGD[/green]")

    try:
        if args.append:
            # Append mode: ensure tables exist but don't drop them
            create_tables(conn, config, drop_existing=False)
            load_data(conn, config, args.scale_factor)
            console.print("\n[green bold]✓ Data appended successfully![/green bold]")
        else:
            if args.create_tables or args.all:
                create_tables(conn, config, drop_existing=True)

            if args.load_data or args.all:
                load_data(conn, config, args.scale_factor)

            console.print("\n[green bold]✓ Demo data generation complete![/green bold]")

        console.print("\nNext steps:")
        console.print(
            "  1. Query from PGD: PGPASSWORD=secret psql -h localhost -p 7432 -U postgres -d demo"
        )
        console.print("  2. Query from WHPG: psql -h localhost -p 5432 -U gpadmin -d demo")
        console.print("  3. Run example queries: python3 scripts/query_examples.py")

    finally:
        conn.close()


if __name__ == "__main__":
    main()
