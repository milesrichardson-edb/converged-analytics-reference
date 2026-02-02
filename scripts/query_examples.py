#!/usr/bin/env python3
"""
Example queries for converged analytics demo.

Runs example queries against PGD and WHPG, demonstrating analytics engine switching.
"""

import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple

try:
    import tomli
except ImportError:
    print("Error: tomli not installed. Run: uv pip install tomli", file=sys.stderr)
    sys.exit(1)

try:
    import psycopg2
except ImportError:
    print("Error: psycopg2 not installed. Run: uv pip install psycopg2-binary", file=sys.stderr)
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


def display_results(title: str, columns: List[str], rows: List[Tuple[Any, ...]]) -> None:
    """Display query results in a formatted table."""
    table = Table(title=title, show_header=True, header_style="bold magenta")

    for col in columns:
        table.add_column(col, style="cyan")

    for row in rows:
        table.add_row(*[str(val) for val in row])

    console.print(table)


def run_query(
    conn: Any, query: str, description: str, show_results: bool = True
) -> List[Tuple[Any, ...]]:
    """Run a query and optionally display results."""
    console.print(f"\n[yellow]Running: {description}[/yellow]")

    start_time = time.time()

    with conn.cursor() as cur:
        cur.execute(query)

        # Only fetch results if the query returns data (not SET, CREATE, etc.)
        if cur.description:
            rows = cur.fetchall()
            columns = [desc[0] for desc in cur.description]

            elapsed_time = time.time() - start_time

            if show_results and rows:
                display_results(description, columns, rows)

            # Display execution time
            console.print(f"[dim]Execution time: {elapsed_time:.3f}s[/dim]")

            return rows
        else:
            # No results to fetch (e.g., SET command)
            elapsed_time = time.time() - start_time
            console.print(f"[dim]Execution time: {elapsed_time:.3f}s[/dim]")
            return []


def query_pgd_transactional(conn: Any) -> None:
    """Run queries against PGD using transactional engine."""
    console.print("\n[bold blue]═══ PGD: Transactional Engine ═══[/bold blue]")

    # Disable analytics engine
    run_query(
        conn,
        "SET bdr.prefer_analytics_engine = false;",
        "Configure: Use transactional engine",
        show_results=False,
    )

    # Row counts
    run_query(
        conn,
        "SELECT COUNT(*) as total_sales FROM demo.sales;",
        "Total sales count",
    )

    # Top countries by revenue
    run_query(
        conn,
        """
        SELECT
            c.country_name,
            COUNT(*) as num_sales,
            SUM(s.revenue) as total_revenue,
            AVG(s.revenue) as avg_revenue
        FROM demo.sales s
        JOIN demo.countries c ON s.country_code = c.country_code
        GROUP BY c.country_name
        ORDER BY total_revenue DESC
        LIMIT 10;
        """,
        "Top 10 countries by revenue (Transactional)",
    )


def query_pgd_analytics(conn: Any) -> None:
    """Run queries against PGD using analytics engine (Iceberg)."""
    console.print("\n[bold green]═══ PGD: Analytics Engine (Iceberg) ═══[/bold green]")

    # Enable analytics engine
    run_query(
        conn,
        "SET bdr.prefer_analytics_engine = true;",
        "Configure: Use analytics engine",
        show_results=False,
    )

    # Total sales count
    run_query(
        conn,
        "SELECT COUNT(*) as total_sales FROM demo.sales;",
        "Total sales count",
    )

    # Top countries by revenue
    run_query(
        conn,
        """
        SELECT
            c.country_name,
            COUNT(*) as num_sales,
            SUM(s.revenue) as total_revenue,
            AVG(s.revenue) as avg_revenue
        FROM demo.sales s
        JOIN demo.countries c ON s.country_code = c.country_code
        GROUP BY c.country_name
        ORDER BY total_revenue DESC
        LIMIT 10;
        """,
        "Top 10 countries by revenue (Analytics/Iceberg)",
    )


def query_whpg_datafusion(conn: Any, config: Dict[str, Any]) -> None:
    """Run queries against WHPG using Datafusion (Seafowl) engine."""
    console.print("\n[bold cyan]═══ WarehousePG: Datafusion Engine ═══[/bold cyan]")

    # Configure Datafusion engine
    run_query(
        conn,
        "SET pgaa.executor_engine = 'seafowl';",
        "Configure: Use Datafusion engine",
        show_results=False,
    )

    # Total sales count
    run_query(
        conn,
        "SELECT COUNT(*) as total_sales FROM demo.sales;",
        "Total sales count",
    )

    # Top countries by revenue
    run_query(
        conn,
        """
        SELECT
            c.country_name,
            COUNT(*) as num_sales,
            SUM(s.revenue) as total_revenue,
            AVG(s.revenue) as avg_revenue
        FROM demo.sales s
        JOIN demo.countries c ON s.country_code = c.country_code
        GROUP BY c.country_name
        ORDER BY total_revenue DESC
        LIMIT 10;
        """,
        "Top 10 countries by revenue (WHPG/Datafusion)",
    )


def query_whpg_spark(conn: Any) -> None:
    """Run queries against WHPG using Spark Connect engine."""
    console.print("\n[bold magenta]═══ WarehousePG: Spark Connect Engine ═══[/bold magenta]")

    # Configure Spark Connect engine
    # Use bridge IP to reach Spark Connect from container
    run_query(
        conn,
        "SET pgaa.executor_engine = 'spark_connect';",
        "Configure: Use Spark engine",
        show_results=False,
    )
    run_query(
        conn,
        "SET pgaa.spark_connect_url = 'sc://172.17.0.1:15002';",
        "Configure: Spark Connect URL",
        show_results=False,
    )

    # Run queries
    run_query(
        conn,
        """
        SELECT
            p.category,
            COUNT(*) as num_sales,
            SUM(s.revenue) as total_revenue,
            SUM(s.profit) as total_profit
        FROM demo.sales s
        JOIN demo.products p ON s.product_id = p.product_id
        GROUP BY p.category
        ORDER BY total_revenue DESC;
        """,
        "Category performance (WHPG/Spark)",
    )

    # Monthly sales trend
    run_query(
        conn,
        """
        SELECT
            DATE_TRUNC('month', s.sale_date) as month,
            COUNT(*) as num_sales,
            SUM(s.revenue) as total_revenue
        FROM demo.sales s
        GROUP BY DATE_TRUNC('month', s.sale_date)
        ORDER BY month;
        """,
        "Monthly sales trend (WHPG/Spark)",
    )


def main() -> None:
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Run example queries against demo databases")
    parser.add_argument(
        "--config",
        "-c",
        type=Path,
        default=Path(__file__).parent.parent / "demo-config.toml",
        help="Path to configuration file",
    )
    parser.add_argument(
        "--pgd-transactional",
        action="store_true",
        help="Run PGD transactional engine queries",
    )
    parser.add_argument(
        "--pgd-analytics", action="store_true", help="Run PGD analytics engine queries"
    )
    parser.add_argument(
        "--whpg-datafusion", action="store_true", help="Run WHPG Datafusion engine queries"
    )
    parser.add_argument(
        "--whpg-spark", action="store_true", help="Run WHPG Spark Connect engine queries"
    )
    parser.add_argument("--all", action="store_true", help="Run all query examples")

    args = parser.parse_args()

    if not (
        args.pgd_transactional
        or args.pgd_analytics
        or args.whpg_datafusion
        or args.whpg_spark
        or args.all
    ):
        parser.print_help()
        sys.exit(1)

    # Load configuration
    config = load_config(args.config)

    try:
        # PGD queries
        if args.pgd_transactional or args.pgd_analytics or args.all:
            console.print("[yellow]Connecting to PGD...[/yellow]")
            pgd_conn = get_db_connection(config)
            console.print("[green]✓ Connected to PGD[/green]")

            if args.pgd_transactional or args.all:
                query_pgd_transactional(pgd_conn)

            if args.pgd_analytics or args.all:
                query_pgd_analytics(pgd_conn)

            pgd_conn.close()

        # WHPG queries
        if args.whpg_datafusion or args.whpg_spark or args.all:
            console.print("\n[yellow]Connecting to WHPG...[/yellow]")
            whpg_conn = get_db_connection(config, analytics=True)
            console.print("[green]✓ Connected to WHPG[/green]")

            if args.whpg_datafusion or args.all:
                query_whpg_datafusion(whpg_conn, config)

            if args.whpg_spark or args.all:
                query_whpg_spark(whpg_conn)

            whpg_conn.close()

        console.print("\n[green bold]✓ All queries completed successfully![/green bold]")

    except Exception as e:
        console.print(f"\n[red bold]Error: {e}[/red bold]")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
