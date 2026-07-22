"""
app/api/v1/router.py
=====================
Master APIRouter that includes all v1 endpoint modules.

All routes share the /api/v1 prefix (set in main.py).
"""
from fastapi import APIRouter

from app.api.v1 import (
    analytics,
    auth,
    disruptions,
    links,
    nodes,
    results,
    scenarios,
    simulation,
)

api_router = APIRouter()

api_router.include_router(auth.router)
api_router.include_router(nodes.router)
api_router.include_router(links.router)
api_router.include_router(scenarios.router)
api_router.include_router(disruptions.router)
api_router.include_router(simulation.router)
api_router.include_router(results.router)
api_router.include_router(analytics.router)
