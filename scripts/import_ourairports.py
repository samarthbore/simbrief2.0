"""
CLI tool to import full OurAirports CSV datasets into the database.
Usage:
    python scripts/import_ourairports.py --airports data/airports.csv --runways data/runways.csv
    python scripts/import_ourairports.py --download
"""

import argparse
import sys
import os
import urllib.request

# Ensure project root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.core.database import SessionLocal, Base, engine
from backend.app.services.aviation_data.importer import OurAirportsImporter
from backend.app.services.aviation_data.seed import seed_database

OURAIRPORTS_AIRPORTS_URL = "https://davidmegginson.github.io/ourairports-data/airports.csv"
OURAIRPORTS_RUNWAYS_URL = "https://davidmegginson.github.io/ourairports-data/runways.csv"


def download_file(url: str, dest_path: str):
    print(f"Downloading from {url} to {dest_path}...")
    urllib.request.urlretrieve(url, dest_path)
    print("Download completed.")


def main():
    parser = argparse.ArgumentParser(description="Import OurAirports aviation dataset")
    parser.add_argument("--airports", help="Path to local airports.csv file")
    parser.add_argument("--runways", help="Path to local runways.csv file")
    parser.add_argument("--download", action="store_true", help="Download latest datasets directly from OurAirports")
    parser.add_argument("--max-airports", type=int, default=None, help="Maximum number of airports to import")
    parser.add_argument("--max-runways", type=int, default=None, help="Maximum number of runways to import")

    args = parser.parse_args()

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    importer = OurAirportsImporter(db)

    airports_path = args.airports
    runways_path = args.runways

    if args.download:
        downloads_dir = os.path.join(os.path.dirname(__file__), "..", "data", "downloads")
        os.makedirs(downloads_dir, exist_ok=True)
        airports_path = os.path.join(downloads_dir, "airports.csv")
        runways_path = os.path.join(downloads_dir, "runways.csv")
        download_file(OURAIRPORTS_AIRPORTS_URL, airports_path)
        download_file(OURAIRPORTS_RUNWAYS_URL, runways_path)

    if airports_path and os.path.exists(airports_path):
        print(f"Importing airports from {airports_path}...")
        with open(airports_path, "r", encoding="utf-8") as f:
            res = importer.import_airports_csv(f, max_records=args.max_airports)
            print(f"Airports import results: {res}")
    else:
        print("No airports file specified or found. Run with --download or provide --airports path.")

    if runways_path and os.path.exists(runways_path):
        print(f"Importing runways from {runways_path}...")
        with open(runways_path, "r", encoding="utf-8") as f:
            res = importer.import_runways_csv(f, max_records=args.max_runways)
            print(f"Runways import results: {res}")

    db.close()
    print("Dataset import completed successfully.")


if __name__ == "__main__":
    main()
