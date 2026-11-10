"""Database seeder script - loads CSV data into SQLite."""

import sys
from pathlib import Path
import pandas as pd

sys.path.append(str(Path(__file__).parent.parent))

from database.db_manager import get_connection, execute_script

DATA_DIR = Path(__file__).parent / "data"
CHUNK_SIZE = 10000


def load_csv_to_db(table_name: str, csv_file: str, chunk: bool = False) -> int:
    """Load CSV file into database table."""
    print(f"Loading {table_name}...")
    df = pd.read_csv(DATA_DIR / csv_file)

    with get_connection() as conn:
        if chunk:
            for i in range(0, len(df), CHUNK_SIZE):
                df.iloc[i:i+CHUNK_SIZE].to_sql(table_name, conn, if_exists='append', index=False)
        else:
            df.to_sql(table_name, conn, if_exists='append', index=False)

    print(f"✓ Loaded {len(df)} {table_name}")
    return len(df)


def seed_database():
    """Initialize schema and load all CSV data."""
    print("=" * 60)
    print("Starting database seeding...")
    print("=" * 60)

    try:
        # Initialize schema
        execute_script(Path(__file__).parent / "schema.sql")
        print("✓ Schema initialized")

        # Load data (vendors first due to foreign keys)
        counts = {
            'vendors': load_csv_to_db('vendors', 'vendors.csv'),
            'inventory': load_csv_to_db('inventory', 'inventory.csv'),
            'finance': load_csv_to_db('finance', 'finance.csv', chunk=True),
            'sales': load_csv_to_db('sales', 'sales.csv', chunk=True)
        }

        # Summary
        print("\n" + "=" * 60)
        print("✓ Seeding completed successfully!")
        for table, count in counts.items():
            print(f"  {table}: {count} records")
        print("=" * 60)

        return True

    except Exception as e:
        print(f"\n{'=' * 60}")
        print(f"✗ Seeding failed: {e}")
        print("=" * 60)
        return False


def main():
    """Main entry point for seeding."""
    return seed_database()


if __name__ == "__main__":
    sys.exit(0 if main() else 1)
