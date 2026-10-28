from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.app.core.config import settings
from backend.app.api.api_router import api_router
from backend.app.services.aviation_data.seed import seed_database


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: ensure tables and standard profiles / sample data exist
    try:
        seed_database()
    except Exception as e:
        print(f"Warning: automatic seed encountered: {e}")
    yield


app = FastAPI(
    title=settings.APP_NAME,
    description="Aviation Flight Planning Platform — REST API for airport search, airway routing, aircraft performance calculations, and briefing generation.",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS if isinstance(settings.CORS_ORIGINS, list) else [settings.CORS_ORIGINS],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/")
def root():
    return {
        "message": f"{settings.APP_NAME} API is active.",
        "docs_url": "/docs",
        "health_url": f"{settings.API_V1_STR}/health",
    }
