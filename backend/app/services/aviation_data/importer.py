import csv
import io
import logging
from datetime import datetime, timezone
from typing import Dict, Any, Optional, TextIO
from sqlalchemy.orm import Session

from backend.app.models.models import (
    Airport,
    Runway,
    DataSource,
    DataImportRun,
)

logger = logging.getLogger(__name__)


def parse_float(val: Optional[str]) -> Optional[float]:
    if val is None or val == "":
        return None
    try:
        return float(val.strip())
    except (ValueError, TypeError):
        return None


def parse_int(val: Optional[str]) -> Optional[int]:
    if val is None or val == "":
        return None
    try:
        return int(float(val.strip()))
    except (ValueError, TypeError):
        return None


def parse_bool(val: Optional[str]) -> bool:
    if not val:
        return False
    return str(val).strip().lower() in ("yes", "1", "true", "t")


class OurAirportsImporter:
    """
    Importer for OurAirports open aviation datasets.
    Supports CSV streams/files for airports.csv and runways.csv.
    """

    def __init__(self, db: Session):
        self.db = db

    def get_or_create_source(self) -> DataSource:
        source = self.db.query(DataSource).filter(DataSource.name == "OurAirports").first()
        if not source:
            source = DataSource(
                name="OurAirports",
                description="Community-maintained database of global airports, runways, and navigation aids.",
                url="https://ourairports.com/data/",
                version="Public Domain / CC0",
                license="Public Domain (Creative Commons CC0 1.0 Universal)",
                attribution="Data sourced from OurAirports (ourairports.com), dedicated to the public domain.",
            )
            self.db.add(source)
            self.db.commit()
            self.db.refresh(source)
        return source

    def import_airports_csv(
        self,
        file_obj: TextIO,
        max_records: Optional[int] = None,
        allowed_types: Optional[set] = None,
    ) -> Dict[str, Any]:
        """
        Import or update airports from OurAirports airports.csv.
        """
        source = self.get_or_create_source()
        run = DataImportRun(
            source_id=source.id,
            dataset_name="airports.csv",
            status="RUNNING",
        )
        self.db.add(run)
        self.db.commit()

        processed = 0
        imported = 0
        skipped = 0
        rejected = 0
        error_logs = []

        reader = csv.DictReader(file_obj)

        for row in reader:
            processed += 1
            if max_records and imported >= max_records:
                break

            ident = (row.get("ident") or "").strip().upper()
            if not ident:
                rejected += 1
                error_logs.append(f"Row {processed}: missing ident")
                continue

            airport_type = (row.get("type") or "").strip().lower()
            if allowed_types and airport_type not in allowed_types:
                skipped += 1
                continue

            lat = parse_float(row.get("latitude_deg"))
            lon = parse_float(row.get("longitude_deg"))

            # Coordinate validation
            if lat is None or lon is None:
                rejected += 1
                error_logs.append(f"Airport {ident}: missing coordinates")
                continue
            if not (-90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0):
                rejected += 1
                error_logs.append(f"Airport {ident}: invalid coordinates ({lat}, {lon})")
                continue

            name = (row.get("name") or ident).strip()
            icao = (row.get("gps_code") or "").strip().upper()
            if not icao and len(ident) == 4 and ident.isalpha():
                icao = ident
            iata = (row.get("iata_code") or "").strip().upper()
            if not iata:
                iata = None

            ourairports_id = parse_int(row.get("id"))
            elevation_ft = parse_float(row.get("elevation_ft"))
            continent = (row.get("continent") or "").strip()
            iso_country = (row.get("iso_country") or "").strip().upper()
            iso_region = (row.get("iso_region") or "").strip().upper()
            municipality = (row.get("municipality") or "").strip()
            scheduled_service = parse_bool(row.get("scheduled_service"))
            gps_code = (row.get("gps_code") or "").strip().upper() or None
            local_code = (row.get("local_code") or "").strip().upper() or None
            home_link = (row.get("home_link") or "").strip() or None
            wikipedia_link = (row.get("wikipedia_link") or "").strip() or None

            existing = self.db.query(Airport).filter(Airport.ident == ident).first()
            if existing:
                existing.ourairports_id = ourairports_id
                existing.icao = icao or existing.icao
                existing.iata = iata or existing.iata
                existing.name = name
                existing.airport_type = airport_type
                existing.latitude = lat
                existing.longitude = lon
                existing.elevation_ft = elevation_ft
                existing.continent = continent
                existing.iso_country = iso_country
                existing.iso_region = iso_region
                existing.municipality = municipality
                existing.scheduled_service = scheduled_service
                existing.gps_code = gps_code
                existing.local_code = local_code
                existing.home_link = home_link
                existing.wikipedia_link = wikipedia_link
            else:
                airport = Airport(
                    ourairports_id=ourairports_id,
                    ident=ident,
                    icao=icao or None,
                    iata=iata,
                    name=name,
                    airport_type=airport_type,
                    latitude=lat,
                    longitude=lon,
                    elevation_ft=elevation_ft,
                    continent=continent,
                    iso_country=iso_country,
                    iso_region=iso_region,
                    municipality=municipality,
                    scheduled_service=scheduled_service,
                    gps_code=gps_code,
                    local_code=local_code,
                    home_link=home_link,
                    wikipedia_link=wikipedia_link,
                )
                self.db.add(airport)

            imported += 1

            if imported % 500 == 0:
                self.db.commit()

        self.db.commit()

        run.status = "COMPLETED"
        run.records_processed = processed
        run.records_imported = imported
        run.records_skipped = skipped
        run.records_rejected = rejected
        run.completed_at = datetime.now(timezone.utc)
        if error_logs:
            run.log_details = "\n".join(error_logs[:50])
        self.db.commit()

        return {
            "run_id": run.id,
            "status": "COMPLETED",
            "processed": processed,
            "imported": imported,
            "skipped": skipped,
            "rejected": rejected,
        }

    def import_runways_csv(
        self,
        file_obj: TextIO,
        max_records: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Import runways from OurAirports runways.csv.
        """
        source = self.get_or_create_source()
        run = DataImportRun(
            source_id=source.id,
            dataset_name="runways.csv",
            status="RUNNING",
        )
        self.db.add(run)
        self.db.commit()

        processed = 0
        imported = 0
        skipped = 0
        rejected = 0
        error_logs = []

        reader = csv.DictReader(file_obj)

        # Cache airport IDs by ident for fast lookup
        airport_map = {a.ident: a.id for a in self.db.query(Airport.ident, Airport.id).all()}

        for row in reader:
            processed += 1
            if max_records and imported >= max_records:
                break

            airport_ident = (row.get("airport_ident") or "").strip().upper()
            if not airport_ident or airport_ident not in airport_map:
                skipped += 1
                continue

            airport_id = airport_map[airport_ident]
            le_ident = (row.get("le_ident") or "").strip()
            he_ident = (row.get("he_ident") or "").strip()

            if not le_ident and not he_ident:
                rejected += 1
                continue

            runway = Runway(
                airport_id=airport_id,
                airport_ident=airport_ident,
                length_ft=parse_float(row.get("length_ft")),
                width_ft=parse_float(row.get("width_ft")),
                surface=(row.get("surface") or "").strip() or None,
                lighted=parse_bool(row.get("lighted")),
                closed=parse_bool(row.get("closed")),
                le_ident=le_ident or None,
                le_latitude=parse_float(row.get("le_latitude_deg")),
                le_longitude=parse_float(row.get("le_longitude_deg")),
                le_elevation_ft=parse_float(row.get("le_elevation_ft")),
                he_ident=he_ident or None,
                he_latitude=parse_float(row.get("he_latitude_deg")),
                he_longitude=parse_float(row.get("he_longitude_deg")),
                he_elevation_ft=parse_float(row.get("he_elevation_ft")),
            )
            self.db.add(runway)
            imported += 1

            if imported % 500 == 0:
                self.db.commit()

        self.db.commit()

        run.status = "COMPLETED"
        run.records_processed = processed
        run.records_imported = imported
        run.records_skipped = skipped
        run.records_rejected = rejected
        run.completed_at = datetime.now(timezone.utc)
        self.db.commit()

        return {
            "run_id": run.id,
            "status": "COMPLETED",
            "processed": processed,
            "imported": imported,
            "skipped": skipped,
            "rejected": rejected,
        }
