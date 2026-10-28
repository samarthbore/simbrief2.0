# Aviation Flight Planner (`aviation-planner`)

A modern, full-stack aviation flight-planning platform inspired by the global 3D world-map experience of Microsoft Flight Simulator and the dispatch capabilities of SimBrief.

Built with **₹0 development budget**: 100% free and open-source tools, downloadable public domain aviation datasets (OurAirports), offline 3D Earth textures (Natural Earth), and zero commercial API keys or subscription tokens required.

---

## Features

- **Interactive 3D Earth Globe**: Powered by CesiumJS with smooth camera flight, orbit, zoom, pan, and airport centering.
- **100% Zero-Cost Offline Rendering**: Configured with public domain Natural Earth textures and ellipsoid fallback—no Cesium ion account or paid tile server needed.
- **Global Airport Database**: Ingestion engine for OurAirports (`airports.csv`, `runways.csv`), normalizing ICAO, IATA, coordinates, and runway configurations.
- **Flight Planning & Routing Engine**:
  - Direct Great Circle navigation arc calculations with intermediate curved waypoints.
  - Multi-objective airway graph search using **Dijkstra** and **A\*** (optimizing for Shortest Distance, Lowest Time, or Lowest Fuel Burn).
  - Admissible Haversine distance heuristic for provably optimal A\* pathfinding.
- **Aircraft Performance Estimation**:
  - Pluggable performance profiles (Airbus A320, Boeing 737-800, Boeing 777-300ER, ATR 72-600, Cessna 172).
  - Calculates En-Route Flight Time (ETE), Trip Fuel, 45-minute statutory IFR reserve, and taxi fuel.
  - Transparent calculation assumptions and operational limitations.
- **Persistence & Audit Revisions**: Save flight plans, audit revision changes, and reopen previous routes.
- **PDF Flight Briefing Export**: Automatically generates an Operational Flight Plan (OFP) briefing PDF using ReportLab with waypoint navigation logs, fuel breakdown, and educational disclaimers.

---

## Technology Stack

| Layer | Technologies |
|---|---|
| **Frontend** | Next.js 14 (App Router), React 18, TypeScript, Tailwind CSS, CesiumJS, Lucide Icons |
| **Backend** | Python 3, FastAPI, SQLAlchemy 2, Pydantic v2, ReportLab, pytest |
| **Database** | SQLite (default out-of-the-box zero-setup) / PostgreSQL with PostGIS support |
| **Data Sources**| OurAirports (Public Domain / CC0), Natural Earth (Public Domain) |

---

## Repository Structure

```text
aviation-planner/
├── backend/
│   ├── app/
│   │   ├── api/                     # REST API route controllers
│   │   │   ├── airports.py          # Airport search, pagination, spatial queries
│   │   │   ├── aircraft.py          # Aircraft performance profile endpoints
│   │   │   ├── routes.py            # Route planning & algorithm comparison
│   │   │   ├── flight_plans.py      # Plan persistence & PDF briefing download
│   │   │   └── health.py            # System healthcheck
│   │   ├── core/                    # App configuration & SQLAlchemy database engine
│   │   ├── models/                  # Database models (Airport, Runway, FlightPlan, etc.)
│   │   ├── schemas/                 # Pydantic v2 validation models
│   │   ├── services/
│   │   │   ├── routing/             # Haversine, Bearing, Dijkstra, and A* algorithms
│   │   │   ├── performance/         # Aircraft performance calculation models
│   │   │   ├── aviation_data/       # CSV data importer and database seeder
│   │   │   └── briefing/            # ReportLab OFP PDF briefing generator
│   │   └── main.py                  # FastAPI application entrypoint & CORS
│   ├── tests/                       # Complete pytest test suite (22 unit & integration tests)
│   ├── requirements.txt             # Backend production dependencies
│   └── requirements-dev.txt         # Testing & development dependencies
├── frontend/
│   ├── public/                      # Static assets & offline CesiumJS build files
│   ├── src/
│   │   ├── app/                     # Next.js App Router (page, layout, globals.css)
│   │   ├── components/
│   │   │   ├── GlobeView.tsx        # CesiumJS 3D Earth component with airport markers & flight arc
│   │   │   ├── FlightPlanPanel.tsx  # Flight dispatch panel with origin/dest autocomplete & metrics
│   │   │   ├── AirportDetailPanel.tsx# Contextual airport inspection & runway information
│   │   │   ├── SavedPlansModal.tsx  # Modal for saved flight plans & revision history
│   │   │   ├── LayerControl.tsx     # Map layer toggles
│   │   │   └── Navbar.tsx           # Application navigation header
│   │   ├── lib/api.ts               # Typed frontend API client
│   │   └── types/index.ts           # TypeScript interfaces
│   ├── package.json                 # Frontend dependencies
│   ├── tailwind.config.js           # Dark aerospace color theme
│   └── tsconfig.json                # TypeScript configuration
├── data/
│   ├── samples/                     # Curated sample airports & runways for tests & instant startup
│   │   ├── airports_sample.csv
│   │   └── runways_sample.csv
│   └── README.md                    # Data source, licence, and attribution documentation
├── scripts/
│   └── import_ourairports.py        # CLI script to download & import full OurAirports data
├── docker-compose.yml               # Optional PostgreSQL/PostGIS container configuration
├── .env.example                     # Environment configuration template
├── pytest.ini                       # Pytest configuration
├── LICENSE                          # Open source MIT license
└── README.md                        # Documentation
```

---

## Quickstart & Local Setup

### Prerequisites

- Python 3.10+ (tested with Python 3.14)
- Node.js 18+ (tested with Node.js 25)
- npm or pnpm

### 1. Backend Setup

```bash
# Clone the repository
git clone https://github.com/your-username/aviation-planner.git
cd aviation-planner

# Create and activate Python virtual environment
python -m venv .venv

# On Windows:
.\.venv\Scripts\activate
# On Linux/macOS:
# source .venv/bin/activate

# Install backend dependencies
pip install -r backend/requirements.txt -r backend/requirements-dev.txt

# Seed the database with sample airports and aircraft profiles
python -m backend.app.services.aviation_data.seed

# Start the FastAPI backend server
uvicorn backend.app.main:app --reload --port 8000
```

The backend API and interactive OpenAPI documentation will be available at:
- **API URL**: `http://localhost:8000`
- **Swagger Docs**: `http://localhost:8000/docs`
- **Health Check**: `http://localhost:8000/api/v1/health`

### 2. Frontend Setup

In a new terminal window:

```bash
cd frontend

# Install dependencies (Cesium, Next.js, Tailwind, Lucide)
npm install

# Start the Next.js development server
npm run dev
```

Open `http://localhost:3000` in your browser to view the interactive 3D flight planner.

---

## Importing Full Global Aviation Datasets

The application comes pre-loaded with sample international hubs (JFK, LHR, CDG, FRA, DXB, DEL, BOM, HND, SYD, etc.). To ingest the complete global database of over 70,000 airports and runways:

```bash
python scripts/import_ourairports.py --download
```

This will automatically stream the official OurAirports CSV files directly into your local database.

---

## Running Automated Tests

Run the comprehensive automated test suite (geometry, routing algorithms, performance estimation, PDF generation, CSV ingestion, and REST API):

```bash
pytest backend/tests -v
```

All 22 test cases verify:
- **Haversine Distance & Bearing**: Known routes (JFK-LHR 2980-3020 NM), cardinal bearings, and great-circle waypoint arc vertex.
- **Routing Algorithms**: Dijkstra and A\* path optimality agreement, admissible heuristic validation, and unreachable destination errors.
- **Aircraft Performance**: Accurate flight time, block fuel, 45-min IFR statutory reserve, and zero-wind groundspeed calculations.
- **PDF Generation**: Binary valid `%PDF` OFP briefing document creation with styling and tables.
- **Database & Importer**: OurAirports CSV validation, coordinate boundaries (-90/90, -180/180), and record error isolation.
- **API Endpoints**: Airport search, autocomplete, plan submission, revision increments, and briefing download.

---

## Algorithm Details & Complexity

### Great Circle Geometry (Haversine Formula)

Calculates the shortest distance over the Earth's spherical surface:
$$\Delta\sigma = 2 \arcsin \sqrt{\sin^2\left(\frac{\Delta\phi}{2}\right) + \cos\phi_1 \cos\phi_2 \sin^2\left(\frac{\Delta\lambda}{2}\right)}$$
$$d = R \cdot \Delta\sigma$$
where $R \approx 3440.065\text{ NM}$ ($6371.009\text{ km}$).

### Pathfinding: Dijkstra vs A\*

- **Dijkstra's Algorithm**: Explores outward radially with time complexity $O((|V| + |E|) \log |V|)$ using a binary min-heap priority queue.
- **A\* Algorithm**: Uses the straight-line Haversine distance to the goal as an admissible heuristic $h(n) \le d^*(n, \text{goal})$. Because straight-line distance is the absolute lower bound on geographic surface distance, the heuristic never overestimates the cost, guaranteeing that A\* finds the optimal route while exploring significantly fewer nodes.

---

## Data Attribution & Licences

1. **OurAirports**: Global airport and runway records licensed under [Creative Commons CC0 1.0 Universal (Public Domain)](https://creativecommons.org/publicdomain/zero/1.0/).
2. **Natural Earth**: Public domain map dataset courtesy of NACIS and cartographic contributors.
3. **CesiumJS**: Licensed under the Apache License 2.0.

---

## Disclaimer

**FOR SIMULATION AND EDUCATIONAL USE ONLY.** This software is intended exclusively for flight simulation and academic study. It is not certified for operational flight planning, dispatch, or real-world navigation.
