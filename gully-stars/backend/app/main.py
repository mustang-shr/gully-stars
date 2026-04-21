"""
Gully Stars API
Grassroots sports management + social platform
FastAPI · Async SQLAlchemy 2.0 · PostgreSQL
"""
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.db.session import engine, Base

# Import all models so Alembic/SQLAlchemy sees them
from app.models import models  # noqa: F401

from app.api.v1.endpoints import (
    auth,
    users,
    teams,
    training,
    matches,
    tournaments,
    feed,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create upload directory
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    # In dev, create tables directly (prod uses Alembic)
    if settings.DEBUG:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(
    title="Gully Stars API",
    description="Grassroots sports platform — team management, tournaments, social feed",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ─── CORS ────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Static file serving (uploads) ───────────────────────────────────────────
os.makedirs("uploads", exist_ok=True)
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# ─── Routers ─────────────────────────────────────────────────────────────────
PREFIX = "/api/v1"

app.include_router(auth.router,        prefix=PREFIX)
app.include_router(users.router,       prefix=PREFIX)
app.include_router(teams.router,       prefix=PREFIX)
app.include_router(training.router,    prefix=PREFIX)
app.include_router(matches.router,     prefix=PREFIX)
app.include_router(tournaments.router, prefix=PREFIX)
app.include_router(feed.router,        prefix=PREFIX)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "gully-stars-api"}


@app.get("/")
async def root():
    return {
        "service": "Gully Stars API",
        "version": "1.0.0",
        "docs": "/docs",
    }
