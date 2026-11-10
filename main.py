"""Main entry point for Inventra CLI."""

import argparse
import sys
import subprocess

import compat  # Python 3.14 + Pydantic compatibility patch — must be first

from agents.coordinator import process_query
from agents.report_agent import get_inventory_status, get_sales_patterns, get_financial_summary
from services.ticket_manager import get_ticket_stats
from config.logger import get_logger

logger = get_logger(__name__)


def run_cli():
    """Run interactive CLI mode."""
    print("=" * 70)
    print("  INVENTRA - AI-Powered Inventory & Financial Management")
    print("=" * 70)
    print("\nWelcome! Type your query or 'quit' to exit.\n")

    while True:
        try:
            query = input("You: ").strip()

            if not query:
                continue

            if query.lower() in ['quit', 'exit', 'q']:
                print("\nThank you for using Inventra. Goodbye!")
                break

            response = process_query(query)
            print(f"\nInventra: {response}\n")

        except KeyboardInterrupt:
            print("\n\nThank you for using Inventra. Goodbye!")
            break
        except Exception as e:
            logger.error(f"Error in CLI: {e}")
            print(f"\nError: {str(e)}\n")


def run_web():
    """Run Streamlit web interface."""

    print("Starting Inventra web interface...")
    print("The app will open in your browser shortly.")
    print("Press Ctrl+C to stop the server.\n")

    subprocess.run([
        sys.executable, "-m", "streamlit", "run",
        "ui/streamlit_app.py",
        "--server.headless", "false"
    ])


def show_stats():
    """Show system statistics."""
    print("=" * 70)
    print("  INVENTRA SYSTEM STATISTICS")
    print("=" * 70)
    print()

    inv = get_inventory_status()
    print(f"INVENTORY:")
    print(f"  Total items: {inv['total_items']}")
    print(f"  Low stock alerts: {inv['low_stock_count']}")
    print()

    sales = get_sales_patterns(days=30)
    if 'error' not in sales:
        print(f"SALES (Last 30 days):")
        print(f"  Total sales: {sales['total_sales']} units")
        print(f"  Revenue: Rs {sales['total_revenue']:,.2f}")
        print()

    finance = get_financial_summary(days=90)
    if 'error' not in finance:
        print(f"FINANCIALS (Last 90 days):")
        print(f"  Total sales: Rs {finance['total_sales']:,.2f}")
        print(f"  Total purchases: Rs {finance['total_purchases']:,.2f}")
        print(f"  Net profit: Rs {finance['net_profit']:,.2f}")
        print(f"  Profit margin: {(finance['net_profit']/finance['total_sales']*100):.1f}%")
        print()

    ticket_stats = get_ticket_stats()
    print(f"TICKETS:")
    print(f"  Pending: {ticket_stats['total_pending']}")
    print(f"  Total value: Rs {ticket_stats['total_value']:,.2f}")
    print()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Inventra - AI-Powered Inventory & Financial Management",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py web              # Launch web interface
  python main.py cli              # Run interactive CLI
  python main.py stats            # Show system statistics

For more information, visit: https://github.com/your-repo/inventra
        """
    )

    parser.add_argument(
        'mode',
        choices=['web', 'cli', 'stats'],
        help='Operation mode'
    )

    args = parser.parse_args()

    try:
        if args.mode == 'web':
            run_web()
        elif args.mode == 'cli':
            run_cli()
        elif args.mode == 'stats':
            show_stats()

    except Exception as e:
        logger.error(f"Fatal error: {e}")
        print(f"\nFatal error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
