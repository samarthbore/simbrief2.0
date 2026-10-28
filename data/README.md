# Aviation Planner — Datasets & Licences Documentation

This directory contains aviation reference data, sample CSVs, and instructions for ingesting open-source datasets.

## 1. OurAirports Data

- **Source**: [OurAirports Data](https://ourairports.com/data/)
- **Licence**: [Creative Commons CC0 1.0 Universal (Public Domain Dedication)](https://creativecommons.org/publicdomain/zero/1.0/)
- **Attribution**: *OurAirports is a free, community-maintained global aviation database. Data is dedicated to the public domain.*
- **Files**:
  - `data/samples/airports_sample.csv`: Sample of 20 major international hubs across 6 continents for automated testing and zero-setup local development.
  - `data/samples/runways_sample.csv`: Runway threshold, surface, and dimension records corresponding to sample airports.
- **Full Ingestion**:
  Run `python scripts/import_ourairports.py --download` to pull the complete worldwide airport database (over 70,000 global airfields and runways).

## 2. Natural Earth World Texture (3D Globe)

- **Source**: [Natural Earth](https://www.naturalearthdata.com/)
- **Licence**: Public Domain
- **Attribution**: *Natural Earth is a public domain map dataset created through the North American Cartographic Information Society (NACIS).*
- **Usage**:
  Bundled locally in `frontend/public/cesium/Assets/Textures/NaturalEarthII/` for completely zero-cost offline 3D Earth rendering without any Cesium ion token or third-party tile subscription.

## 3. Aircraft Performance Estimates

- **Source**: Standard manufacturer Pilot Operating Handbooks (POH) and Aircraft Flight Manuals (AFM) simplified educational parameters.
- **Disclaimer**: *Parameters (cruise speed, fuel flow, service ceiling) represent nominal educational approximations. Not valid for real-world flight dispatch or operational navigation.*
