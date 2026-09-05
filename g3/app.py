"""RETRACT G3 editorial desk — FastAPI + static UI. Local only."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

import ops

G3_ROOT = Path(__file__).resolve().parent
STATIC = G3_ROOT / "static"

app = FastAPI(title="RETRACT G3", docs_url=None, redoc_url=None)


class CorrectBody(BaseModel):
    day: str = Field(default="Monday")
    reason: str = Field(default="Calendar confirmed Monday.", min_length=1)


class DisputeBody(BaseModel):
    reason: str = Field(
        default="Launch day disputed; treat as not established.", min_length=1
    )


@app.on_event("startup")
def _startup() -> None:
    ops.ensure_seeded()


@app.get("/api/health")
def api_health() -> dict[str, Any]:
    return {"ok": True, "service": "retract-g3"}


@app.get("/api/state")
def api_state() -> dict[str, Any]:
    return ops.get_state()


@app.post("/api/reset")
def api_reset() -> dict[str, Any]:
    return ops.reset_and_seed()


@app.post("/api/correct")
def api_correct(body: CorrectBody) -> dict[str, Any]:
    try:
        return ops.correct(day=body.day, reason=body.reason)
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
    except RuntimeError as e:
        raise HTTPException(409, str(e)) from e


@app.post("/api/dispute")
def api_dispute(body: DisputeBody) -> dict[str, Any]:
    try:
        return ops.dispute(reason=body.reason)
    except ValueError as e:
        raise HTTPException(400, str(e)) from e
    except RuntimeError as e:
        raise HTTPException(409, str(e)) from e


# Back-compat aliases
@app.get("/api/graph")
def api_graph() -> dict[str, Any]:
    return ops.get_state()


@app.post("/api/seed")
def api_seed() -> dict[str, Any]:
    return ops.reset_and_seed()


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC / "index.html")


app.mount("/static", StaticFiles(directory=str(STATIC)), name="static")
