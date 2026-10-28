import io
from backend.app.core.database import SessionLocal, Base, engine
from backend.app.models.models import Airport, DataSource, DataImportRun
from backend.app.services.aviation_data.importer import OurAirportsImporter


def test_import_airports_csv_valid_and_invalid():
    db = SessionLocal()
    try:
        importer = OurAirportsImporter(db)

        # CSV with 1 valid airport, 1 invalid coordinates, 1 missing ident
        sample_csv = io.StringIO(
            "id,ident,type,name,latitude_deg,longitude_deg,elevation_ft,continent,iso_country,iso_region,municipality,scheduled_service,gps_code,iata_code,local_code,home_link,wikipedia_link,keywords\n"
            "99901,TEST1,large_airport,Test Airport One,12.34,56.78,100,AS,IN,IN-DL,Delhi,yes,TEST,T1,,,,\n"
            "99902,TEST2,large_airport,Test Bad Lat,195.0,20.0,50,AS,IN,IN-MH,Mumbai,no,BAD1,,,,, \n"
            "99903,,medium_airport,Test No Ident,10.0,20.0,50,AS,IN,IN-KA,Bangalore,no,,,,,, \n"
        )

        res = importer.import_airports_csv(sample_csv)
        assert res["status"] == "COMPLETED"
        assert res["imported"] >= 1
        assert res["rejected"] >= 2

        imported_airport = db.query(Airport).filter(Airport.ident == "TEST1").first()
        assert imported_airport is not None
        assert imported_airport.name == "Test Airport One"
        assert imported_airport.latitude == 12.34
        assert imported_airport.longitude == 56.78
        assert imported_airport.scheduled_service is True

        # Check DataSource metadata
        ds = db.query(DataSource).filter(DataSource.name == "OurAirports").first()
        assert ds is not None
        assert "CC0" in ds.license
    finally:
        db.close()
