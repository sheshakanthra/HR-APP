"""FastAPI application entrypoint.

Milestone 1: boots, validates secrets, exposes health. Auth/directory/leave/
policy/agent routers are wired in later milestones.
"""

from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("peopledesk")


def create_app() -> FastAPI:
    # Fail fast on missing/placeholder secrets before serving any request.
    settings.validate_secrets()

    app = FastAPI(
        title="PeopleDesk API",
        version="0.1.0",
        description="HRMS with a core AI agent. Modules added per milestone.",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.web_origin],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health", tags=["meta"])
    def health() -> dict:
        return {"status": "ok", "env": settings.app_env}

    # Routers (registered as milestones land):
    from app.api.routes import admin, auth

    app.include_router(auth.router)
    app.include_router(admin.router)
    # directory / leave / policy / agent land in later milestones.

    logger.info("PeopleDesk API initialized (env=%s)", settings.app_env)
    return app


app = create_app()
