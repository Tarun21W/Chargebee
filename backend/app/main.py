"""FastAPI application entrypoint for the Customer Intelligence Agent AI layer."""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.logging import configure_logging, get_logger

configure_logging()
log = get_logger("app.main")

app = FastAPI(
    title="Customer Intelligence Agent — AI Service",
    version="0.1.0",
    description="RAG, summarisation, risk scoring, timeline and multi-agent layer.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["system"])
def health() -> dict:
    return {"status": "ok", "service": "customer-intelligence-agent"}


# ---- Routers ---------------------------------------------------------------
from app.api.routers import (  # noqa: E402
    admin,
    agents,
    alerts,
    analytics,
    chat,
    customers,
    graph,
    ingest,
    risk,
    summary,
    timeline,
)

for module in (
    customers,
    summary,
    chat,
    risk,
    timeline,
    agents,
    graph,
    ingest,
    alerts,
    analytics,
    admin,
):
    app.include_router(module.router)

log.info("Customer Intelligence Agent AI service initialised.")
