#!/usr/bin/env python3
"""
Wait for PGD to finish replicating data to analytics (Iceberg).

This script blocks until all WAL records have been replicated to the analytics slot.
Useful for scripting when you need to ensure data is available in Iceberg before proceeding.
"""

import sys
from pathlib import Path
from typing import Any, Dict

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
    from rich.live import Live
    from rich.spinner import Spinner
    from rich.text import Text
except ImportError:
    print("Error: rich not installed. Run: uv pip install rich", file=sys.stderr)
    sys.exit(1)

import time
import threading


console = Console()


def load_config(config_path: Path) -> Dict[str, Any]:
    """Load TOML configuration file."""
    with open(config_path, "rb") as f:
        return tomli.load(f)


def get_db_connection(config: Dict[str, Any]) -> Any:
    """Get database connection to PGD."""
    db_config = config["database"]["transactional"]

    # For PGD, use port 7432 (exposed port)
    return psycopg2.connect(
        host="localhost",
        port=7432,
        database=db_config["database"],
        user=db_config["user"],
        password=db_config["password"],
    )


def wait_for_replication(conn: Any) -> None:
    """Wait for analytics replication to complete with visual progress indicator."""
    start_time = time.time()

    # Create spinner with elapsed time
    spinner = Spinner("dots", text="Waiting for analytics replication to complete...")

    # Flag to track completion
    completed = threading.Event()
    error_msg = None

    def run_wait():
        nonlocal error_msg
        with conn.cursor() as cur:
            try:
                cur.execute(
                    "SELECT bdr.wait_slot_confirm_lsn(bdr.local_analytics_slot_name(), null);"
                )
                conn.commit()
            except Exception as e:
                error_msg = str(e)
            finally:
                completed.set()

    # Start the wait operation in a separate thread
    wait_thread = threading.Thread(target=run_wait, daemon=True)
    wait_thread.start()

    # Show spinner with elapsed time if running interactively
    if sys.stdout.isatty():
        with Live(spinner, console=console, refresh_per_second=10) as live:
            while not completed.is_set():
                elapsed = time.time() - start_time
                minutes, seconds = divmod(int(elapsed), 60)
                time_str = f"{minutes}m {seconds}s" if minutes > 0 else f"{seconds}s"
                spinner.update(
                    text=f"Waiting for analytics replication to complete... ({time_str})"
                )
                time.sleep(0.1)
    else:
        # Non-interactive mode: just print and wait
        console.print("[yellow]Waiting for analytics replication to complete...[/yellow]")
        wait_thread.join()

    # Wait for thread to complete
    wait_thread.join()

    # Report result
    elapsed = time.time() - start_time
    minutes, seconds = divmod(int(elapsed), 60)
    time_str = f"{minutes}m {seconds}s" if minutes > 0 else f"{seconds}s"

    if error_msg:
        console.print(f"[red]✗ Error waiting for replication: {error_msg}[/red]")
        raise Exception(error_msg)
    else:
        console.print(f"[green]✓ Analytics replication complete (took {time_str})[/green]")


def main() -> None:
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Wait for PGD analytics replication to complete")
    parser.add_argument(
        "--config",
        "-c",
        type=Path,
        default=Path(__file__).parent.parent / "demo-config.toml",
        help="Path to configuration file",
    )
    parser.add_argument(
        "--timeout",
        "-t",
        type=int,
        help="Optional timeout in seconds (not currently implemented - query will wait indefinitely)",
    )

    args = parser.parse_args()

    # Load configuration
    config = load_config(args.config)

    # Connect to PGD
    console.print("[yellow]Connecting to PGD...[/yellow]")
    conn = get_db_connection(config)
    console.print("[green]✓ Connected to PGD[/green]")

    try:
        wait_for_replication(conn)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
