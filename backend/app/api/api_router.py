from fastapi import APIRouter
from backend.app.api import health, airports, aircraft, routes, flight_plans

api_router = APIRouter()

api_router.include_router(health.router, tags=["Health"])
api_router.include_router(airports.router, tags=["Airports"])
api_router.include_router(aircraft.router, tags=["Aircraft"])
api_router.include_router(routes.router, tags=["Routing"])
api_router.include_router(flight_plans.router, tags=["Flight Plans"])
