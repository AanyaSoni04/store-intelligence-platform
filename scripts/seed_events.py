"""
Synthetic event seeder — populates the database with realistic test data.

Usage:
    python -m scripts.seed_events --store store_001 --visitors 50 --hours 8

TODO: Implement:
    - Generate realistic visitor journeys (ENTRY → zones → queue → EXIT)
    - Randomize dwell times, zone visits, queue participation
    - Include some staff visitors (is_staff=True)
    - Include some re-entries
    - Include some queue abandonment
    - Write events to the database via the API or directly
"""

import argparse
import logging

logger = logging.getLogger("store_intel")


def main():
    parser = argparse.ArgumentParser(description="Seed the database with synthetic events")
    parser.add_argument("--store", default="store_001", help="Store ID")
    parser.add_argument("--visitors", type=int, default=50, help="Number of visitors to simulate")
    parser.add_argument("--hours", type=int, default=8, help="Hours of activity to simulate")
    parser.add_argument("--db-url", default="sqlite:///data/store_intel.db", help="Database URL")
    args = parser.parse_args()

    print(f"Seeding {args.visitors} visitors over {args.hours}h for store {args.store}")

    # TODO: Implement event generation logic
    # TODO: Create store and visitor records
    # TODO: Generate realistic event sequences
    # TODO: Write to database

    print("TODO: Seeder not yet implemented")


if __name__ == "__main__":
    main()
